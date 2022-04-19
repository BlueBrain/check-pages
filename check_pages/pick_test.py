"""Tests for 'pick-real-neuron'.
"""
from selenium.webdriver.common.by import By


class PickNeuronTests:
    """Defines the Testing class for 'pick-real-neuron'."""

    # These URL lead to the simui pages.
    URL = "https://bbp.epfl.ch/pick-real-neuron/"
    TEXT_REAL = "that is a real neuron"
    TEXT_SYNTH = "that is a synthesized neuron"

    def __init__(self, driver):
        """Initializes this test object with the seleniumbase-seleniumwire webdriver."""
        # The driver
        self.driver = driver

    def open(self):
        """Open the main page."""
        self.driver.open(self.URL)

    def click_image(self, correct=True):
        """Click on image and check outcome."""

        # Do we want correct or incorrect guess?
        if correct:
            xpath = "(//img)[3]"
            txt = self.TEXT_REAL
        else:
            xpath = "(//img)[4]"
            txt = self.TEXT_SYNTH

        # Check image properties
        image = self.driver.find_element(xpath, by=By.XPATH)
        image_src = image.get_attribute("src")
        assert image_src.endswith(".jpeg")
        print(f"Image source: {image_src}   Image size: {image.size}")
        assert image.size["height"] > 300

        # Click on image
        self.driver.click(xpath)

        # Check for correct overlay text
        for _ in range(20):
            if self.driver.is_text_visible(txt):
                return
        assert False

    def check_score(self, score):
        """Check the given 'score'."""
        self.driver.find_element(f"//div[text()='{score}']", by=By.XPATH)

    def perform_test(self):
        """Performs the actual test by opening the page and clicking on two images."""
        self.open()
        print("\n")

        # Click on correct image
        self.click_image(True)
        self.check_score(2)

        # Click on incorrect image
        self.click_image(False)
        self.check_score(3)

        # Quit the browser
        self.driver.tearDown()


def test_pickneuron(selbase):
    """Wrapper for the tests."""
    ebrains = PickNeuronTests(selbase)
    ebrains.perform_test()
