import json
from pathlib import Path
import tempfile
import unittest
try:
    from PIL import Image
except ImportError:  # Pillow is part of the optional vision extras (requirements-vision*.txt), not of CI
    Image = None
from tools.ball_patch_data import run
from tools.metrica_data import sha256


@unittest.skipIf(Image is None, 'Pillow (optional vision extras) not installed')
class PatchDataTests(unittest.TestCase):
    def test_grid_is_reference_independent_and_recheck_not_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);native=root/'native';native.mkdir()
            manifest={'version':'synthetic-native','provided_fixture_used':False,'images':[],
                      'splits':{},'annotation_sha256':{}}
            for split,game in [('train','4'),('valid','6'),('test','9')]:
                folder=native/split;folder.mkdir()
                image=folder/'clip_000001.jpg';Image.new('RGB',(64,64),'green').save(image)
                coco={'images':[{'id':17,'file_name':image.name,'width':64,'height':64}],
                      'annotations':[{'id':1,'image_id':17,'category_id':1,'bbox':[2,2,4,4]}],
                      'categories':[{'id':1,'name':'ball'}]}
                annotation=folder/'_annotations.coco.json';annotation.write_text(json.dumps(coco))
                manifest['annotation_sha256'][split]=sha256(annotation)
                manifest['splits'][split]={'games':[game]}
                manifest['images'].append({'file':split+'/'+image.name,'sha256':sha256(image)})
            (native/'manifest.json').write_text(json.dumps(manifest))
            plan={'version':'synthetic-patches','source_dataset_version':'synthetic-native',
                  'provided_fixture_used':False,'seed':731,'tile_size':32,'tile_overlap':0,
                  'source_frame_modulus':100,'train_games':['4'],'validation_games':['6'],'fixed_recheck_games':['9']}
            path=root/'plan.json';path.write_text(json.dumps(plan))
            first=run(native,path,root/'first')
            self.assertEqual(first['counts']['train']['patches'],2)
            self.assertEqual(first['counts']['valid']['patches'],4)
            self.assertEqual(first['counts']['train']['reference_free_patches'],1)
            self.assertFalse((root/'first/test').exists())
            self.assertEqual(first['selected_native_images']['test'][0]['id'],17)
            annotation=native/'valid/_annotations.coco.json'
            coco=json.loads(annotation.read_text());coco['annotations'][0]['bbox']=[40,40,4,4]
            annotation.write_text(json.dumps(coco));manifest['annotation_sha256']['valid']=sha256(annotation)
            (native/'manifest.json').write_text(json.dumps(manifest))
            second=run(native,path,root/'second')
            self.assertEqual({k:v for k,v in first['image_sha256'].items() if k.startswith('valid/')},
                             {k:v for k,v in second['image_sha256'].items() if k.startswith('valid/')})
            self.assertNotEqual(first['annotation_sha256']['valid'],second['annotation_sha256']['valid'])
