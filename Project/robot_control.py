"""
Use this only for testing/AI logic if you have to use Python.

"""

import requests


class DamanRobot:
    def __init__(self, robot_ip: str, port: int = 8088):
        self.base_url = f"http://{robot_ip}:{port}"

    def _move(self, command: str, amount: int = 0, speed: int = 200):
        data = {
            "command": command,
            "amount": amount,
            "speed": speed,
        }
        response = requests.post(
            f"{self.base_url}/manual/base",
            json=data,
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def forward(self, cm: int):
        return self._move("forward", max(2, min(cm, 50)))

    def backward(self, cm: int):
        return self._move("backward", max(2, min(cm, 50)))

    def left(self, degrees: int):
        return self._move("left", max(1, min(degrees, 90)))

    def right(self, degrees: int):
        return self._move("right", max(1, min(degrees, 90)))

    def stop(self):
        return self._move("stop", 0)


if __name__ == "__main__":
    # CHANGE THIS to your DAMAN robot/bridge IP.
    robot = DamanRobot("192.168.1.50")

    # Simple test sequence:
    print(robot.forward(20))
    print(robot.left(90))
    print(robot.forward(20))
    print(robot.stop())
