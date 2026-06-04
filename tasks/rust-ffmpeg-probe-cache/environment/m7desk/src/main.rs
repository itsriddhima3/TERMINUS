use std::env;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("usage: m7desk run-stress --manifest <path> --output <path>");
        process::exit(2);
    }
    match args[1].as_str() {
        "run-stress" => {
            if let Err(e) = m7desk::cmd::stress::run_from_args(&args[2..]) {
                eprintln!("run-stress failed: {e}");
                process::exit(1);
            }
        }
        other => {
            eprintln!("unknown subcommand: {other}");
            process::exit(2);
        }
    }
}
