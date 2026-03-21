import time

class LLMController:
    def __init__(self, input_file_handler, output_file_handler):
        self.input_file_handler = input_file_handler
        self.output_file_handler = output_file_handler
    
    def prompt(self):
        try:
            input_text = self.input_file_handler.readFile()
            
            # insert llm logic/call here
            # Writes to output as llm returns stream
        
            output_text = ("apple", "banana", "cherry", "example", "output", "text", "here")

            self.output_file_handler.clearFile()

            for token in output_text:
                time.sleep(1)
                self.output_file_handler.appendToFile(token + " ")
            
            return True
        except Exception as e:
            print("LLM Controller Error: ", e)
            return False