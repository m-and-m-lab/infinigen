python -m infinigen_examples.generate_indoors --seed 0 --task coarse --output_folder outputs/indoors/coarse_multi_room_2 -g fast_solve.gin singleroom.gin -p compose_indoors.terrain_enabled=False &&
python -m infinigen.tools.export --input_folder outputs/indoors/coarse_multi_room_2 --output_folder outputs/omniverse/coarse_multi_room_2 -f usdc -r 1024 --omniverse
