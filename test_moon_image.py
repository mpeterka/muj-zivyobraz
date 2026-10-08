import io
import unittest

from PIL import Image

from functions.moon_image import parse_options, phase_mask, render_moon


class MoonImageTests(unittest.TestCase):
    def test_defaults_and_styles(self):
        self.assertEqual(parse_options(''), (128, 128, 'voyage'))
        self.assertEqual(parse_options('style=real&height=256&width=128'), (128, 256, 'real'))
        self.assertEqual(parse_options('width=1024&height=32'), (1024, 32, 'voyage'))

    def test_invalid_queries(self):
        for query in ['style=other', 'style=REAL', 'width=31', 'height=1025',
                      'width=0128', 'width=+128', 'width=%31%32%38', 'width=',
                      'width=128&width=256', 'style=real&style=voyage',
                      'height=128&height=128', 'foo=bar', 'width=128&',
                      'style=real;width=128', 'width=128&style=real&height=128&foo=1']:
            with self.subTest(query=query), self.assertRaises(ValueError):
                parse_options(query)

    def test_mask_cardinal_phases_and_sides(self):
        for angle, left, right in [(0, 0, 0), (90, 0, 255),
                                   (180, 255, 255), (270, 255, 0)]:
            mask = phase_mask(101, angle)
            with self.subTest(angle=angle):
                self.assertEqual(mask.getpixel((25, 50)), left)
                self.assertEqual(mask.getpixel((75, 50)), right)
                self.assertEqual(mask.getpixel((0, 0)), 0)

    def test_crescents_are_smaller_than_quarters(self):
        count = lambda angle: sum(phase_mask(101, angle).get_flattened_data())
        self.assertLess(count(30), count(90))
        self.assertLess(count(330), count(270))
        self.assertAlmostEqual(count(90), count(270), delta=101 * 255)

    def test_png_dimensions_palette_and_real_credit(self):
        for style in ['voyage', 'real']:
            for size in [(128, 128), (256, 128), (1024, 1024)]:
                with self.subTest(style=style, size=size):
                    image = Image.open(io.BytesIO(render_moon(*size, style, 90)))
                    self.assertEqual(image.size, size)
                    self.assertEqual(image.mode, '1')
                    self.assertEqual(image.getpixel((0, 0)), 255)
                    if style == 'real':
                        self.assertIn('Luc Viatour', image.info['Author'])
                        self.assertIn('by-sa/3.0', image.info['License'])

    def test_new_moon_has_no_bright_rocket(self):
        for style in ['voyage', 'real']:
            image = Image.open(io.BytesIO(render_moon(128, 128, style, 0)))
            full = Image.open(io.BytesIO(render_moon(128, 128, style, 180)))
            self.assertLess(sum(image.get_flattened_data()), sum(full.get_flattened_data()))

    def test_renderer_rejects_untrusted_arguments(self):
        for width, height, style, angle in [(1025, 128, 'real', 90),
                (128, 128, '../source', 90), (128, 128, 'real', float('nan'))]:
            with self.assertRaises(ValueError):
                render_moon(width, height, style, angle)


if __name__ == '__main__':
    unittest.main()
