import unittest
from ticket_fields import extract_text_fields,normalize_row
from pricing import comparable,seat_mask

class FieldTests(unittest.TestCase):
    def test_chinese_headers_combined_fields_and_actual_row_notes(self):
        cases=[('区域: F4 排数: 12 座位号: 1X',('F4','12','1X')),('F4区15/16/17排 X 5内',('F4','15/16/17','X')),('T03区 B排 12内',('T03','B','')),('F13区 15排 实际第11排 X',('F13','15','X')),('F12구역 8열 2x번',('F12','8','2X')),('区域 F4 排号 十二 座位号 2X',('F4','12','2X')),('序号 T11 区域 101 排数 O 座位号 2X',('101','O','2X'))]
        for text,expected in cases:
            with self.subTest(text=text):
                fields=extract_text_fields(text)
                self.assertEqual(tuple(fields[k] for k in ['section','row','seat_as_printed']),expected)
        self.assertEqual(normalize_row('排数：１２排'),'12')
        self.assertEqual(normalize_row('M(9)'),'M(9)')
        self.assertEqual(extract_text_fields('区域 F4 排数 未知 座位号 1X')['row'],'')
    def test_comparable_masks_are_exact_and_rows_within_three(self):
        a=dict(id='a',section='F4',row='12',seat_as_printed='1X',price=4000,sold=False,currency='CNY',concert='NCT WISH',performance_date='2027-01-15')
        b={**a,'id':'b','row':'15','price':3500}
        self.assertTrue(comparable(a,b))
        for change in [dict(row='16'),dict(seat_as_printed='2X'),dict(seat_as_printed='X'),dict(performance_date='2027-01-16'),dict(performance_date=None),dict(row='11/12'),dict(sold=True),dict(superseded_by=80),dict(availability='paid_in_source')]:
            self.assertFalse(comparable(a,{**b,**change}),change)
        self.assertEqual(seat_mask('1X(3内)'),'1X')
        self.assertIsNone(seat_mask('X/2X'))
