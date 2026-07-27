import unittest
import pandas as pd
import os

class TestDataQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load datasets once for all tests."""
        print("⚙️ Loading datasets for quality assurance...")
        cls.df_acc = pd.read_csv('../accounts_data.csv')
        cls.df_con = pd.read_csv('../contracts_data.csv')
        cls.df_logs = pd.read_csv('../daily_usage_logs.csv')
        cls.df_csm = pd.read_csv('../csm_rep_data.csv')
        cls.df_health = pd.read_csv('../account_health_data.csv')

    def test_file_existence(self):
        """Verify all required CSV files exist."""
        files = ['accounts_data.csv', 'contracts_data.csv', 'daily_usage_logs.csv', 'csm_rep_data.csv', 'account_health_data.csv']
        for file in files:
            self.assertTrue(os.path.exists(f'../{file}'), f"Missing file: {file}")

    def test_row_counts(self):
        """Verify data generation meets the strict case study specifications."""
        self.assertEqual(len(self.df_acc), 1000, "Accounts table must have exactly 1,000 rows.")
        self.assertEqual(len(self.df_csm), 50, "CSM table must have exactly 50 rows.")
        self.assertGreaterEqual(len(self.df_con), 1000, "Contracts table must have at least 1,000 rows.")
        self.assertEqual(len(self.df_health), 52000, "Account Health must have 52,000 rows (weekly snapshots).")
        self.assertGreaterEqual(len(self.df_logs), 150000, "Daily Logs should have ~200,000 rows.")

    def test_no_null_critical_values(self):
        """Ensure critical financial and identification columns are not null."""
        self.assertEqual(self.df_con['annual_commit_dollars'].isnull().sum(), 0)
        self.assertEqual(self.df_acc['account_id'].isnull().sum(), 0)
        self.assertEqual(self.df_health['health_color'].isnull().sum(), 0)

    def test_financial_logic(self):
        """Ensure Contract ARR is strictly positive."""
        self.assertTrue((self.df_con['annual_commit_dollars'] > 0).all(), "Found contracts with 0 or negative ARR.")

    def test_health_color_validity(self):
        """Ensure qualitative health scores only contain allowed values."""
        allowed_colors = {'Green', 'Yellow', 'Red'}
        actual_colors = set(self.df_health['health_color'].unique())
        self.assertTrue(actual_colors.issubset(allowed_colors), "Found invalid health colors in data.")

if __name__ == '__main__':
    unittest.main(verbosity=2)