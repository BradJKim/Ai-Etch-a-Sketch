class KeyboardController:
    def __init__(self, device='/dev/input/event0'):
        self.device = device

    def grabInputChar(self):
        try:
            with open(self.device, 'rb') as f:
                data = f.read(24)
                return data
        except Exception as e:
            print("Keyboard Controller Error:", e)
            return False