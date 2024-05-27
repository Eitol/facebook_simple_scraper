import unittest
from facebook_simple_scraper.tests.utils import MockRequester


class TestMockRequester(unittest.TestCase):

    def test_multiple_requests(self):
        mock_requester = MockRequester()
        mock_requester.clear()
        # Set up mock response
        self.maxDiff = None
        resp_text_1 = 'text1'
        status_code_1 = 200
        resp_headers_1 = {'header': 'value'}
        resp_text_2 = 'text2'
        status_code_2 = 400
        resp_headers_2 = {'header2': 'value2'}

        # Añadir respuestas esperadas
        mock_requester.add_expected_response(resp_text_1, status_code_1, resp_headers_1)
        self.assertEqual(len(mock_requester.responses), 1)
        mock_requester.add_expected_response(resp_text_2, status_code_2, resp_headers_2)
        self.assertEqual(len(mock_requester.responses), 2)

        # Comprobar las respuestas añadidas
        self.assertEqual(mock_requester.responses[0].text, resp_text_1)
        self.assertEqual(mock_requester.responses[0].status_code, status_code_1)
        self.assertEqual(mock_requester.responses[0].headers, resp_headers_1)
        self.assertEqual(mock_requester.responses[1].text, resp_text_2)
        self.assertEqual(mock_requester.responses[1].status_code, status_code_2)
        self.assertEqual(mock_requester.responses[1].headers, resp_headers_2)

        # Hacer solicitudes y verificar las respuestas
        r1 = mock_requester.request('GET', 'https://test1.com')
        self.assertEqual(len(mock_requester.last_request_history), 1)
        self.assertEqual(r1.text, resp_text_1)
        self.assertEqual(r1.status_code, status_code_1)
        self.assertEqual(r1.headers, resp_headers_1)

        r2 = mock_requester.request('GET', 'https://test2.com')
        self.assertEqual(len(mock_requester.last_request_history), 2)
        self.assertEqual(r2.text, resp_text_2)
        self.assertEqual(r2.status_code, status_code_2)
        self.assertEqual(r2.headers, resp_headers_2)


if __name__ == "__main__":
    unittest.main()
