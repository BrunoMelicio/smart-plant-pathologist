import asyncio
import unittest
from unittest.mock import patch
import httpx
from PIL import Image
from app import app
from inspection import measure_image
from pathologist_engine import PlantPathologistClient

class InspectionTests(unittest.TestCase):
    def test_color_area_and_localized_coordinates(self):
        img = Image.new('RGB', (100, 100), 'green')
        img.paste((230,200,20), (10,20,30,40))
        r = measure_image(img)
        self.assertEqual(r['metrics'][0]['coverage'], 4.0)
        box = r['regions'][0]
        self.assertEqual((box['x'], box['y'], box['width'], box['height']), (.1,.2,.2,.2))
        self.assertEqual(box['coverage'], 4.0)

    def test_no_candidates_on_green(self):
        r = measure_image(Image.new('RGB',(100,100),'green'))
        self.assertEqual(r['regions'], [])
        self.assertEqual(r['metrics'][0]['coverage'], 0)

    def test_negated_symptoms_are_not_positive(self):
        result = PlantPathologistClient()._synthesize_diagnosis('A healthy monstera. No black spots, yellowing, or pest damage.')
        self.assertEqual(result.severity, 'Healthy')

    def test_sparse_model_output_is_undetermined(self):
        result = PlantPathologistClient()._synthesize_diagnosis('1. Monster Plant (Plantae)')
        self.assertEqual(result.severity, 'Undetermined')
        self.assertEqual(result.visual_symptoms, [])

    def test_endpoint_contract_and_bad_inputs(self):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
                self.assertEqual((await c.post('/diagnose')).status_code,400)
                bad = await c.post('/diagnose',files={'image':('bad.jpg',b'not an image','image/jpeg')})
                self.assertEqual(bad.status_code,422)
                self.assertEqual((await c.get('/')).status_code,200)
                fake = PlantPathologistClient()._synthesize_diagnosis('The leaf is yellow with brown spots.')
                with patch('app.pathologist_client.diagnose_plant',return_value=fake) as model:
                    res = await c.post('/diagnose',data={'sample_key':'healthy'})
                    self.assertEqual(res.status_code,200)
                    data=res.json()
                    self.assertIsNone(data['probability'])
                    self.assertEqual(data['severity'],'High') # sample label did not override observation
                    self.assertEqual(model.call_args.args[1],None)
                    self.assertIn('metrics',data)
                    self.assertIn('regions',data)
        asyncio.run(run())

if __name__=='__main__':
    unittest.main()
