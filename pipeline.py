import argparse
from lib.classify import main as classify_main
from lib.link import process_unlinked

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Orchestrator")
    parser.add_argument("command", choices=["classify", "link", "process"], help="Command to run")
    args = parser.parse_args()
    
    if args.command == "classify":
        classify_main()
    elif args.command == "link":
        process_unlinked()
    elif args.command == "process":
        classify_main()
        process_unlinked()
        
if __name__ == "__main__":
    main()
