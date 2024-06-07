# `cllm-gen-dalle` CLI Tool Documentation

`cllm-gen-dalle` is a command-line tool for generating images using OpenAI's DALL-E model. Below are the details on how to use the CLI arguments.

## Usage

```sh
cllm-gen-dalle [OPTIONS]
```

## Options

- `-m, --model <model>`: 
  - **Description**: Specifies the model to use for image generation.
  - **Default**: `dall-e-3`
  - **Example**: `--model dall-e-2`

- `-s, --size <size>`: 
  - **Description**: Specifies the size of the generated images.
  - **Default**: `1024x1024`
  - **Valid Options**: `256x256`, `512x512`, `1024x1024`
  - **Example**: `--size 512x512`

- `-q, --quality <quality>`: 
  - **Description**: Specifies the quality of the generated images.
  - **Default**: `standard`
  - **Valid Options**: `low`, `standard`, `high`
  - **Example**: `--quality high`

- `-n, --number <number>`: 
  - **Description**: Specifies the number of images to generate per prompt.
  - **Default**: `1`
  - **Example**: `--number 3`

- `-sp, --style <style>`: 
  - **Description**: Additional styling prompt to generate images from.
  - **Default**: `""` (empty string)
  - **Example**: `--style "impressionist"`

- `-o, --output-dir <output-dir>`: 
  - **Description**: Directory to save generated images.
  - **Default**: `None`
  - **Example**: `--output-dir ./images`

## Example Command

```sh
echo '["A futuristic cityscape", "A serene mountain landscape"]' | cllm-gen-dalle --model dall-e-3 --style "cyberpunk"
```

This command will generate images for the prompts "A futuristic cityscape" and "A serene mountain landscape" using the DALL-E 3 model, with a size of 512x512 pixels, high quality, and in a cyberpunk style. It will generate 2 images per prompt and save them in the `./generated_images` directory.
