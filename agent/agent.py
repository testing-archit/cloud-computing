from flask import Flask, request, jsonify
import docker
import os
import random
import logging
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = docker.from_env()

@app.get('/health')
def health():
    """Health check endpoint."""
    try:
        return jsonify({
            "status": "ok",
            "host": os.environ.get('AGENT_HOST', 'localhost'),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.post('/start_container')
def start_container():
    """Start a container with resource limits."""
    try:
        data = request.get_json()
        image = data.get('image')
        cpu = data.get('cpu', 1)
        memory = data.get('memory', '2g')
        port = data.get('port', 8888)
        user_id = data.get('user_id')
        
        if not image:
            return jsonify({"error": "Missing image parameter"}), 400
        
        container_name = f"compute_{user_id}_{random.randint(10000,99999)}"
        
        # Pull image if not present
        try:
            client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling image: {image}")
            client.images.pull(image)
        
        # Run container with resource limits
        container = client.containers.run(
            image,
            detach=True,
            name=container_name,
            ports={f'{port}/tcp': port},
            mem_limit=memory,
            cpu_quota=int(cpu * 100000),
            environment={
                'USER_ID': str(user_id),
                'CONTAINER_PORT': str(port)
            },
            labels={
                'user_id': str(user_id),
                'managed_by': 'compute_booking'
            }
        )
        
        url = f"http://{os.environ.get('AGENT_HOST','localhost')}:{port}"
        logger.info(f"Container started: {container_name} on port {port}")
        
        return jsonify({
            "container_name": container_name,
            "url": url,
            "port": port
        }), 200
        
    except docker.errors.ImageNotFound as e:
        return jsonify({"error": f"Image not found: {image}"}), 400
    except docker.errors.ContainerError as e:
        return jsonify({"error": f"Container error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Failed to start container: {e}")
        return jsonify({"error": str(e)}), 500

@app.post('/stop_container/<container_name>')
def stop_container(container_name):
    """Stop and remove a container."""
    try:
        container = client.containers.get(container_name)
        container.stop(timeout=10)
        container.remove()
        logger.info(f"Container stopped: {container_name}")
        return jsonify({"msg": "Container stopped", "name": container_name}), 200
    except docker.errors.NotFound:
        return jsonify({"error": "Container not found"}), 404
    except Exception as e:
        logger.error(f"Failed to stop container: {e}")
        return jsonify({"error": str(e)}), 500

@app.get('/containers')
def list_containers():
    """List all managed containers."""
    try:
        filters = {'label': 'managed_by=compute_booking'}
        containers = client.containers.list(filters=filters)
        return jsonify([{
            "id": c.id[:12],
            "name": c.name,
            "status": c.status,
            "labels": c.labels
        } for c in containers]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post('/test_image/<image>')
def test_image(image):
    """Test if an image can be pulled."""
    try:
        client.images.pull(image)
        return jsonify({"msg": f"Image {image} available"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to pull image: {e}"}), 400

if __name__ == '__main__':
    host = os.environ.get('AGENT_HOST', '0.0.0.0')
    port = int(os.environ.get('AGENT_PORT', 5000))
    logger.info(f"Starting agent on {host}:{port}")
    app.run(host=host, port=port, debug=False)
