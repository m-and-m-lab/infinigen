python -m infinigen_examples.generate_indoors --seed 1 --task coarse --output_folder infinigen_outputs/indoors/coarse_multiroom -g multiroom.gin -p compose_indoors.terrain_enabled=False &&
python -m infinigen.tools.export --input_folder infinigen_outputs/indoors/coarse_multiroom --output_folder infinigen_outputs/omniverse/coarse_multiroom -f usdc -r 1024 --omniverse
