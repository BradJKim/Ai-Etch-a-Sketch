from enum import Enum

class DisplayMode(Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

class LCDController:
    def __init__(self, input_file_handler, output_file_handler):
        self.input_file_handler = input_file_handler
        self.output_file_handler = output_file_handler

    def writeToScreen(self, text):
        print(text)

    def displayScreen(self, displayMode):
        try:
            if displayMode not in [m.value for m in DisplayMode]:
                raise ValueError(f"Invalid mode '{displayMode}'. Choose from: {DisplayMode}")
            
            if displayMode == DisplayMode.INPUT.value:
                displayText = self.input_file_handler.readFile()
            elif displayMode == DisplayMode.OUTPUT.value:
                displayText = self.output_file_handler.readFile()

            self.writeToScreen(displayText)
            
            return True
        except Exception as e:
            print("LCD Controller Error: ", e)
            return False