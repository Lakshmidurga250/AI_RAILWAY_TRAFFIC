"""Standalone Background Simulation & Optimization Worker Process."""
import time
import signal
import sys
from simulation.engine.simulator import sim_engine

running = True

def handle_shutdown(signum, frame):
    global running
    print(f"[WORKER] Received signal {signum}. Shutting down worker cleanly...")
    running = False

def run_worker():
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    print("[WORKER] AI Railway Background Simulation & Optimization Worker started.")
    sim_engine.start()

    cycle = 0
    while running:
        time.sleep(1.0)
        cycle += 1
        if cycle % 30 == 0:
            status = sim_engine.get_status_summary()
            print(f"[WORKER HEARTBEAT] Sim Time: {status['current_sim_time']} | Active Trains: {status['total_trains']} | Conflicts: {status['active_conflicts']}")

    sim_engine.stop()
    print("[WORKER] Worker terminated successfully.")

if __name__ == "__main__":
    run_worker()
