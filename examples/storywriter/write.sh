#!/bin/bash
set -e

VERSION=v1
FILE_PATH="tmp/story/${VERSION}"
CHAT_CONTEXT="story-${VERSION}"

PROMPT_SYSTEM="You are a story book author." 
PROMPT_CONTEXT="Your task is to gather information from the user 
and write a story based on the information.
You can ask the user for the following information: 
1. Name of the main character 
2. Age of the main character 
3. Description of the main character 
4. Setting of the story 
5. Problem that the main character faces 
6. How the main character solves the problem 
7. The ending of the story"
PROMPT_INSTRUCTIONS="Ask the user one question at a time. 
Say 'done' when you are finished. When finished do not output the story
until the user asks for it.
When you are ready introduce yourself and ask the first question."

mkdir -p ${FILE_PATH}

cllm \
--chat-context "${CHAT_CONTEXT}" \
--prompt-system "${PROMPT_SYSTEM}" \
--prompt-instructions "${PROMPT_INSTRUCTIONS}" \
gpt/4o "${PROMPT_CONTEXT}"

echo "When done, type 'done' to quit"
while true; do
    read -p "You: " input
    if [ "$input" == "done" ]; then
        break
    fi
    response=$(cllm -c ${CHAT_CONTEXT} gpt/4o "${input}")
    echo "Author: ${response}"
    if [[ "${response}" == *"done"* ]]; then
        break
    fi
done

echo "Generating the story"
cllm -c ${CHAT_CONTEXT} \
--prompt-output "Markdown format" \
--prompt-example "
Paragraph 1

Paragraph 2

# The End
" \
--prompt-instructions "Output the story" \
gpt/4o > ${FILE_PATH}/story.md

STORY_PATH=${FILE_PATH}/story.md

echo "Generating edit suggestions for the story"
cat ${STORY_PATH} | cllm \
--prompt-role "You are story book editor" \
--prompt-instructions "Make suggestions on how to improve this story as a bullet list" \
--prompt-output "Markdown format" \
--prompt-example "- Suggestion 1
- Suggestion 2
- Suggestion 3" \
gpt/4o > ${FILE_PATH}/suggestions.md

SUGGESTION_PATH=${FILE_PATH}/suggestions.md

cat ${SUGGESTION_PATH}

read -p "Do you want to apply the suggestions to the story? (yes/no): " apply_suggestions
if [ "$apply_suggestions" == "yes" ]; then
    cat ${SUGGESTION_PATH} | cllm \
    --prompt-role "You are story book editor" \
    --prompt-instructions "Apply the following suggestions to the story.
    $(cat ${FILE_PATH}/suggestions.md)
    " \
    --prompt-output "Markdown format" \
    --prompt-example "# Title

    Paragraph 1

    Paragraph 2

    # The End" \
    gpt/4o > ${FILE_PATH}/story-edit.md

    STORY_PATH=${FILE_PATH}/story-edit.md
fi

PROMPT_PATH=${FILE_PATH}/prompts.json

echo "Generating prompts for the story"
cat ${STORY_PATH} | \
cllm \
--schema list \
--prompt-system "You are book illustrator" \
--prompt-instructions "For each paragraph come up with a text to image prompt that goes along with the paragraph
Be very detailed about the physical apperance of the characters in each prompt." \
gpt/4o > ${PROMPT_PATH}

echo "Generating images for the story"
echo "This cloud take a while depending on the number of images"

IMAGE_PATH=${FILE_PATH}/images
mkdir -p ${IMAGE_PATH}
cat ${PROMPT_PATH} | cllm-gen-dalle -o ${IMAGE_PATH}

echo "Combining the story with the images and prompts to produce the final product"
cat ${STORY_PATH} | cllm \
--prompt-role "You are book editor" \
--prompt-instructions "
Combine the story with the images and prompts to produce the final product.
Each image will go with a paragraph in the story.

IMAGE:
$(ls ${IMAGE_PATH})

PROMPTS:
$(cat ${PROMPT_PATH})
" \
--prompt-output "Markdown format" \
--prompt-example "# Title

Paragraph 1

![image prompt 0](images/image_0.png)

Paragraph 2

![image prompt 1](images/image_1.png)

Paragraph 3

![Image prompt 3](images/image_3.png)

# The End" \
gpt/4o > ${FILE_PATH}/story-final.md

cat ${FILE_PATH}/story-final.md