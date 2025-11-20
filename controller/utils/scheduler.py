from controller.utils.wol import wake_on_lan
import datetime
import requests
import logging

logger = logging.getLogger(__name__)

def schedule_jobs(scheduler, app):
    @scheduler.scheduled_job('interval', minutes=1)
    def job_checker():
        # import models inside job to avoid circular import during module import time
        from controller.models import db, Booking, Agent
        with app.app_context():
            try:
                now = datetime.datetime.utcnow()

                # Check agent health every minute
                check_agent_health(db, Agent)

                # Wake machines 10 min early
                wake_time = now + datetime.timedelta(minutes=10)
                wake_list = Booking.query.filter(
                    Booking.start_time <= wake_time,
                    Booking.start_time > now,
                    Booking.status == "approved"
                ).all()

                for b in wake_list:
                    agent = Agent.query.get(b.agent_id)
                    if agent and agent.wol_enabled:
                        try:
                            wake_on_lan(agent.mac)
                            logger.info(f"[Wake-on-LAN] {agent.ip}")
                        except Exception as e:
                            logger.error(f"WoL failed for {agent.id}: {e}")

                # Start sessions
                start_list = Booking.query.filter(
                    Booking.start_time <= now,
                    Booking.status == "approved"
                ).all()

                for b in start_list:
                    agent = Agent.query.get(b.agent_id)
                    if not agent or agent.status != "online":
                        continue
                    try:
                        # Allocate resources
                        port = 8000 + b.id % 1000
                        res = requests.post(
                            f"http://{agent.ip}:{agent.port}/start_container",
                            json={
                                "user_id": b.user_id,
                                "image": b.image,
                                "cpu": b.cpu,
                                "memory": b.memory,
                                "port": port
                            },
                            timeout=15
                        )
                        if res.status_code == 200:
                            res_json = res.json()
                            b.status = "active"
                            b.access_url = res_json.get("url")
                            b.container_name = res_json.get("container_name")
                            
                            # Update agent resources
                            agent.available_cpu -= b.cpu
                            agent.available_mem -= int(b.memory.rstrip('gm'))
                            
                            db.session.commit()
                            logger.info(f"[STARTED] Booking {b.id} on {agent.ip}")
                        else:
                            logger.error(f"Failed to start booking {b.id}: {res.status_code}")
                    except requests.Timeout:
                        logger.warning(f"Timeout starting booking {b.id} on agent {agent.id}")
                    except Exception as e:
                        logger.error(f"Failed to start booking {b.id}: {e}")

                # Stop expired sessions
                stop_list = Booking.query.filter(
                    Booking.end_time <= now,
                    Booking.status == "active"
                ).all()

                for b in stop_list:
                    agent = Agent.query.get(b.agent_id)
                    if not agent:
                        continue
                    try:
                        requests.post(
                            f"http://{agent.ip}:{agent.port}/stop_container/{b.container_name}",
                            timeout=15
                        )
                        b.status = "completed"
                        
                        # Free up resources
                        agent.available_cpu += b.cpu
                        agent.available_mem += int(b.memory.rstrip('gm'))
                        
                        db.session.commit()
                        logger.info(f"[STOPPED] Booking {b.id}")
                    except Exception as e:
                        logger.error(f"Failed to stop booking {b.id}: {e}")
            except Exception as e:
                logger.error(f"Scheduler job failed: {e}")

def check_agent_health(db, Agent):
    """Poll all agents for health status every minute."""
    agents = Agent.query.all()
    for agent in agents:
        try:
            res = requests.get(
                f"http://{agent.ip}:{agent.port}/health",
                timeout=5
            )
            if res.status_code == 200:
                agent.status = "online"
                agent.last_seen = datetime.datetime.utcnow()
            else:
                agent.status = "offline"
        except requests.Timeout:
            agent.status = "offline"
            logger.warning(f"Agent {agent.id} health check timeout")
        except Exception as e:
            agent.status = "offline"
            logger.warning(f"Agent {agent.id} health check failed: {e}")
    
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to update agent health: {e}")
        db.session.rollback()
