from config_models import ADSEConfig
import subprocess
import analyzer
import argparse

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ADSE Configuration Explorer')
    parser.add_argument('--config', type=str, required=True, 
                        help='Path to the ADSE configuration JSON file')
    
    args = parser.parse_args()
    
    config = ADSEConfig.from_json_file(args.config)

    print("\nGenerating all configuration combinations:\n")
    all_configs = config.parameters.generate_all_configurations()
    print(f"Total Configuration: {len(all_configs)}")

    base_sniper_cli_command = "$run_sniper_path -v --power -n 1 -c $cfgfile $config -d $outdir  --roi -- $benchmark_path -p 1"

    cfg_idx = 1
    for cfg in all_configs:
        cfg_args = cfg.to_cli_args()
        config_as_string = " ".join(cfg_args)

        new_sniper_config = base_sniper_cli_command
        new_sniper_config = new_sniper_config.replace("$run_sniper_path", config.run_sniper_path)
        new_sniper_config = new_sniper_config.replace("$cfgfile", config.cfgfile)
        new_sniper_config = new_sniper_config.replace("$config", config_as_string)
        new_sniper_config = new_sniper_config.replace("$outdir", f"{config.output_dir}/configuration_{cfg_idx}")
        new_sniper_config = new_sniper_config.replace("$benchmark_path", config.benchmark_path)

        print(f"\nConfiguration {cfg_idx}:")
        print(new_sniper_config)

        command = [
            f"{config.run_sniper_path}",
            "-v",
	    "--power",
            "-n","1",
            "-c", f"{config.cfgfile}",
        ]

        for override in cfg_args:
            command.extend(["-c", override])

        command += [
            "-d", f"{config.output_dir}/configuration_{cfg_idx}",
            "--",config.benchmark_path,
            "-p", "1"
        ]

        result = subprocess.run(command, check=True)

        cfg_idx += 1
    
    print("Finish running all configurations, analyzing results")
    analyzer.analyse_results(config.output_dir)


        
