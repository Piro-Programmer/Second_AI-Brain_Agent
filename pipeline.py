import argparse
from lib.classify import main as classify_main
from lib.link import process_unlinked
from lib.build_graph import export_graph

def run_full_pipeline():
    """Execute full SecondSelf pipeline: classify -> link -> graph rebuild."""
    classify_main()
    process_unlinked()
    return export_graph()

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Orchestrator")
    parser.add_argument("command", choices=["classify", "link", "graph", "process"], help="Command to run")
    args = parser.parse_args()
    
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
