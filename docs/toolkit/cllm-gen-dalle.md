# `cllm-gen-dalle` Command Documentation

## Overview
The `cllm-gen-dalle` command is a tool for generating images using OpenAI's DALL-E model. It allows users to specify various parameters such as model type, image size, quality, and number of images to generate. The generated images can be saved locally if an output directory is specified.

## Usage
```sh
cllm-gen-dalle [OPTIONS]
```

## Options
- `-m`, `--model` (type: `str`, default: `"dall-e-3"`): Specifies the model to use for image generation.
- `-s`, `--size` (type: `str`, default: `"1024x1024"`): Specifies the size of the generated images. Valid options are `"256x256"`, `"512x512"`, and `"1024x1024"`.
- `-q`, `--quality` (type: `str`, default: `"standard"`): Specifies the quality of the generated images. Valid options are `"low"`, `"standard"`, and `"high"`.
- `-n`, `--number` (type: `int`, default: `1`): Specifies the number of images to generate per prompt. Must be at least `1`.
- `-sp`, `--style` (type: `str`, default: `""`): Additional styling prompt to generate images from.
- `-o`, `--output-dir` (type: `str`, default: `None`): Directory to save generated images.

## Input
The command reads JSON input from `stdin`, which should be a list of prompts for image generation.

## Output
The command outputs a JSON array of URLs of the generated images. If an error occurs, it outputs a JSON object with an `error` key.

## Example
### Command
```sh
echo '["A futuristic cityscape", "A serene mountain landscape"]' | cllm-gen-dalle -m "dall-e-3" -s "512x512" -q "high" -n 2 -sp "in the style of Van Gogh" -o "./output_images"
```

### Explanation
- Generates 2 images for each prompt ("A futuristic cityscape" and "A serene mountain landscape") using the "dall-e-3" model.
- The images are of size "512x512" and of "high" quality.
- The images are styled "in the style of Van Gogh".
- The generated images are saved in the `./output_images` directory.

## Detailed Steps
1. **Argument Parsing**: The command-line arguments are parsed using `argparse`.
2. **Validation**: The provided arguments are validated to ensure they are within the acceptable range.
3. **Reading Prompts**: The command reads JSON input from `stdin` to get the list of prompts.
4. **Image Generation**: Asynchronously generates images for each prompt using the specified parameters.
5. **Saving Images**: If an output directory is specified, the generated images are saved locally.
6. **Output**: The URLs of the generated images are printed as a JSON array.

## Error Handling
- If the input JSON is invalid, an error message is logged and a JSON object with an `error` key is printed.
- If any other error occurs during execution, it is logged and a JSON object with an `error` key is printed.

## Logging
The command uses the `logging` module to log information and errors. The log level can be set using the `LOGLEVEL` or `CLLM_LOGLEVEL` environment variables.

## Dependencies
- `openai`
- `aiohttp`
- `requests`
- `argparse`
- `asyncio`
- `json`
- `os`
- `sys`
- `logging`

## Environment Variables
- `LOGLEVEL` or `CLLM_LOGLEVEL`: Sets the logging level.

## Notes
- Ensure you have the necessary API keys and permissions to use OpenAI's DALL-E model.
- The command requires an active internet connection to fetch the generated images.
- Generating images costs API credits, so use the command judiciously.
