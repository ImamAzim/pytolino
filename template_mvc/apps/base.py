from template_mvc.controllers.base import ExampleController
from template_mvc.views.base import ExampleView


def main():
    pass


def example():
    app = ExampleApp()
    app.start()


class ExampleApp(object):

    """example app"""

    def __init__(self):
        """
        construct the app
        """

        view = ExampleView()
        controller = ExampleController(view)
        view.set_controller(controller)
        self._view = view

    def start(self):
        self._view.start()


if __name__ == '__main__':
    main()
