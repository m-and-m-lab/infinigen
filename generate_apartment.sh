python -m infinigen_examples.generate_indoors --seed 0 --task populate --output_folder infinigen_outputs/indoors/coarse_multiroom -g fast_solve.gin singleroom.gin -p compose_indoors.terrain_enabled=False &&
python -m infinigen.tools.export --input_folder infinigen_outputs/indoors/coarse_multiroom --output_folder infinigen_outputs/omniverse/coarse_multiroom -f usdc -r 1024 --omniverse
