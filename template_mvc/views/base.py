def main():
    pass


class ExampleView(object):

    """view"""

    def __init__(self):
        self._controller = None
        self._menu = {
                '1': 'option 1',
                'q': 'quit',
                }
        self._running = True

    def set_controller(self, controller):
        """
        Set the controller
        :param controller:
        :return:
        """
        self._controller = controller

    def start(self):
        self._print_welcome()
        while self._running:
            self._print_menu()
            choice = input('please select:\n')
            if choice in self._menu:
                getattr(self, f'case_{choice}')()

    def _print_welcome(self):
        print(
                'welcome to an example app'
                )
        print('===')

    def _print_menu(self):
        for key, value in self._menu.items():
            print(key, value)
        print('===')

    def case_1(self):
        """change path

        """
        print('you have chosen option 1')
        print('===')

    def case_q(self):
        """quit

        """
        print('goodbye')
        self._running = False


if __name__ == '__main__':
    main()
