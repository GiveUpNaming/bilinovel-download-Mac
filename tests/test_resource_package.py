import unittest

from resource.book import book_base64
from resource.logo import logo_base64
from resource.logo_big import logo_big_base64


class ResourcePackageTest(unittest.TestCase):
    def test_embedded_images_are_importable(self):
        self.assertTrue(book_base64)
        self.assertTrue(logo_base64)
        self.assertTrue(logo_big_base64)


if __name__ == '__main__':
    unittest.main()
