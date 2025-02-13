import sys

from application.bin.systemd_agent_service import agent_service

if __name__ == "__main__":
    try:
        agent_service.main()
    except KeyboardInterrupt:
        sys.exit(0)
