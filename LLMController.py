from FileHandler import FileHandler
import ollama


class LLMController:
    def __init__(self, input_file_handler, output_file_handler):
        self.input_file_handler = input_file_handler
        self.output_file_handler = output_file_handler

    def prompt(self):
        try:
            input_text = self.input_file_handler.readFile()

            system_instructions = (
                "Explain as a helpful instructor. "
                "Do not use emojis. "
                "Keep the response to 80 words or fewer. "
                "If you are unsure, say you are unsure instead of making things up."
            )

            """ response = ollama.chat(
                model="qwen2.5:7b-instruct",
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": input_text}
                ],
                options={
                    "temperature": 0
                }
            ) """

            # output_text = response["message"]["content"].strip()
            output_text = input_text
            
            self.output_file_handler.clearFile()
            self.output_file_handler.appendToFile(output_text)

            return True

        except Exception as e:
            print("LLM Controller Error:", e)
            return False