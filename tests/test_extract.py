# -*- coding: utf-8 -*-

"""Tests for PyOBO."""

import unittest

import pandas as pd

from pyobo import get_filtered_xrefs, get_id_name_mapping, get_xrefs_df
from tests.constants import TEST_CHEBI_OBO_PATH


class TestMapping(unittest.TestCase):
    """Test extrating information."""

    def test_get_names(self):
        """Test getting names"""
        id_to_name = get_id_name_mapping('chebi', url=TEST_CHEBI_OBO_PATH, local=True)
        for identifier in id_to_name:
            self.assertFalse(identifier.startswith('CHEBI'))
            self.assertFalse(identifier.startswith('CHEBI:'))
            self.assertFalse(identifier.startswith('chebi:'))
            self.assertFalse(identifier.startswith('chebi'))

    def test_get_xrefs(self):
        """Test getting xrefs."""
        df = get_xrefs_df('chebi', url=TEST_CHEBI_OBO_PATH, local=True)
        self.assertIsInstance(df, pd.DataFrame)

        for key, value in df[['source_ns', 'source_id']].values:  # no need for targets since are external
            self.assertFalse(value.startswith(key))
            self.assertFalse(value.lower().startswith(key.lower()), msg=f'Bad value: {value}')
            self.assertFalse(value.startswith(f'{key}:'))
            self.assertFalse(value.lower().startswith(f'{key.lower()}:'))

    def test_get_target_xrefs(self):
        """Test getting xrefs."""
        kegg_xrefs = get_filtered_xrefs('chebi', 'kegg', url=TEST_CHEBI_OBO_PATH, local=True)
        print(kegg_xrefs)

        for key, value in kegg_xrefs.items():
            self.assertFalse(key.startswith('CHEBI:'))
            self.assertFalse(key.startswith('CHEBI'))
            self.assertFalse(key.startswith('chebi:'))
            self.assertFalse(key.startswith('chebi'))
            self.assertFalse(value.startswith('KEGG:'))
            self.assertFalse(value.startswith('KEGG'))
            self.assertFalse(value.startswith('kegg:'))
            self.assertFalse(value.startswith('kegg'))

        self.assertIsInstance(kegg_xrefs, dict)
