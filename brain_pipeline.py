import argparse
import lib.config as config
from lib.classify import main as classify_main
from lib.link import process_unlinked
from lib.build_graph import export_graph

def run_full_pipeline(username: str = None):
    """Execute full SecondSelf pipeline: classify -> link -> graph rebuild."""
    username = username or config.get_user()
    classify_main(username)
    process_unlinked(username)
    return export_graph(username)

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Orchestrator")
    parser.add_argument("command", choices=["classify", "link", "graph", "process"], help="Command to run")
    parser.add_argument("--user", type=str, default="default", help="Username to process")
    args = parser.parse_args()
    config.set_user(args.user)

    if args.command == "classify":
        classify_main()
    elif args.command == "link":
        process_unlinked()
    elif args.command == "graph":
        export_graph()
    elif args.command == "process":
        run_full_pipeline()

if __name__ == "__main__":
    main()
