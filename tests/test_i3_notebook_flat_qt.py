"""Flat Qt artwork must not retain upstream metallic gradients on controls."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import darfinos_control as control

SVG = 'http://www.w3.org/2000/svg'


class FlatQtArtworkTests(unittest.TestCase):
    def render(self, contents):
        return ET.fromstring(control._notebook_kvantum_svg(
            ('<svg xmlns="'+SVG+'">' + contents + '</svg>').encode(), '#ffcb2e'))

    def test_widget_surfaces_are_flat_but_transparency_and_geometry_are_preserved(self):
        tree = self.render('''
          <defs><linearGradient id="metal"><stop stop-color="#eee"/><stop offset="1" stop-color="#222"/></linearGradient></defs>
          <g id="button-normal"><path d="M0 0h20v20H0z" style="fill:url(#metal)"/>
            <path d="M0 0h20v5H0z" style="opacity:.37;fill:url(#metal)"/></g>
          <path id="toolbar-normal" opacity=".58" fill="url(#metal)" d="M1 2h10"/>
          <path id="scrollbarslider-focused" style="fill:url(#metal);stroke:url(#metal);stroke-width:1"/>
          <path id="lineedit-normal" style="fill:url(#metal)"/>
          <path id="arrow-down-normal" style="fill:#f2f2f2" d="M1 1h2"/>
        ''')
        button = next(node for node in tree if node.get('id') == 'button-normal')
        self.assertEqual([node.get('style') for node in button],
                         ['fill:#2c313a', 'opacity:.37;fill:#2c313a'])
        self.assertEqual(button[0].get('d'), 'M0 0h20v20H0z')
        toolbar = next(node for node in tree if node.get('id') == 'toolbar-normal')
        self.assertEqual(toolbar.get('fill'), '#20242b')
        self.assertEqual(toolbar.get('opacity'), '.58')
        scrollbar = next(node for node in tree if node.get('id') == 'scrollbarslider-focused')
        self.assertEqual(scrollbar.get('style'), 'fill:#9299a5;stroke:#9299a5;stroke-width:1')
        arrow = next(node for node in tree if node.get('id') == 'arrow-down-normal')
        self.assertEqual(arrow.get('d'), 'M1 1h2')
        self.assertEqual(arrow.get('style'), 'fill:#f2f2f2')
        self.assertIsNotNone(tree.find(f'{{{SVG}}}defs/{{{SVG}}}linearGradient'))

    def test_state_colors_keep_selected_controls_and_checked_glyph_distinct(self):
        tree = self.render('''
          <path id="button-focused" style="fill:url(#metal)"/>
          <path id="button-toggled" style="fill:url(#metal)"/>
          <path id="progress-normal" style="fill:url(#metal)"/>
          <path id="tab-toggled-top" style="fill:url(#metal)"/>
          <g id="checkbox-checked-normal"><rect style="fill:url(#metal)"/>
             <path style="fill:url(#metal)"/></g>
        ''')
        nodes = {node.get('id'): node for node in tree}
        self.assertEqual(nodes['button-focused'].get('style'), 'fill:#39404b')
        self.assertEqual(nodes['button-toggled'].get('style'), 'fill:#4b4333')
        self.assertEqual(nodes['progress-normal'].get('style'), 'fill:#ffcb2e')
        self.assertEqual(nodes['tab-toggled-top'].get('style'), 'fill:#ffcb2e')
        self.assertEqual([child.get('style') for child in nodes['checkbox-checked-normal']],
                         ['fill:#2c313a', 'fill:#ffcb2e'])
        self.assertEqual(nodes['slider-toggled'].get('fill'), '#ffcb2e')
        self.assertEqual(nodes['slider-normal'].get('fill'), '#303641')

    def test_flat_theme_disables_embossed_text_without_replacing_palette(self):
        settings = (Path(control.__file__).parent / 'themes/i3-notebook/kvantum.ini').read_text()
        self.assertIn('[PanelButtonCommand]\ntext.shadow=false', settings)
        self.assertIn('button.color=#2c313a', settings)
        self.assertIn('highlight.color={{ .accent }}', settings)

    def test_solid_bevel_layers_are_flat_while_empty_outlines_remain_empty(self):
        tree = self.render('''
          <g id="tabframe-normal-top"><path style="opacity:.15;fill:#fff" d="M0 0h20v2H0z"/>
            <path style="fill:#5a5a5a;fill-opacity:.3" d="M0 2h20v2H0z"/>
            <path style="opacity:.4" d="M0 4h20v2H0z"/>
            <path style="fill: none;stroke:#555" d="M0 0h20v6H0z"/></g>
        ''')
        frame = next(node for node in tree if node.get('id') == 'tabframe-normal-top')
        self.assertEqual([node.get('fill') for node in list(frame)[:3]], ['#20242b'] * 3)
        self.assertIn('opacity:.15', frame[0].get('style'))
        self.assertIn('fill-opacity:.3', frame[1].get('style'))
        self.assertEqual(frame[3].get('style'), 'fill: none;stroke:#555')
        self.assertIsNone(frame[3].get('fill'))
