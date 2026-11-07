import importlib.util
import json
from pathlib import Path
import pickle
import tempfile
import unittest

from tools.visual_long_review import clock_start, concatenate, run
from development.visual_possession import VisualCamera
from test_visual_possession import CFG, frame, context


class LongReviewTests(unittest.TestCase):
    def test_automatic_match_start_is_not_video_start(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'clock.jsonl'
            p.write_text('\n'.join(json.dumps({'status':'observed_clock','clock_s':c,
                'video_time_s':449+c,'human_annotated':False}) for c in (1,7,13)))
            self.assertEqual(clock_start(p),449)

    def test_unstable_or_human_clock_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'clock.jsonl'
            p.write_text(json.dumps({'status':'observed_clock','clock_s':1,'video_time_s':450,'human_annotated':True}))
            with self.assertRaises(ValueError):clock_start(p)

    def test_checkpoint_preserves_temporal_owner_confirmation(self):
        whole,part=VisualCamera(CFG),VisualCamera(CFG)
        for f in range(3):
            p=frame(f);whole.consume(p,context(p));part.consume(p,context(p))
        restored=pickle.loads(pickle.dumps(part))
        for f in range(3,8):
            p=frame(f)
            self.assertEqual(whole.consume(p,context(p)),restored.consume(p,context(p)))

    def test_local_review_required(self):
        with self.assertRaises(ValueError):run('unused','unused','unused','unused','unused','unused')

    @unittest.skipUnless(importlib.util.find_spec('supervision'),'Optional vision runtime')
    def test_actual_bytetrack_state_roundtrip_without_deprecated_class_pickle(self):
        import numpy as np
        import supervision as sv
        a,b=sv.ByteTrack(),sv.ByteTrack()
        for i in range(3):
            detection=sv.Detections(xyxy=np.array([[10+i,10,30+i,50]],np.float32),
                                    confidence=np.array([.9]),class_id=np.array([0]))
            a.update_with_detections(detection)
        state=pickle.loads(pickle.dumps(a.__dict__))
        b.__dict__.update(state)
        detection=sv.Detections(xyxy=np.array([[14,10,34,50]],np.float32),
                                confidence=np.array([.9]),class_id=np.array([0]))
        np.testing.assert_array_equal(a.update_with_detections(detection).tracker_id,
                                      b.update_with_detections(detection).tracker_id)

    @unittest.skipUnless(importlib.util.find_spec('av'),'Optional AV runtime')
    def test_remux_keeps_all_frames_and_native_clock(self):
        import av
        import numpy as np
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);parts=[]
            for index in range(2):
                path=root/f'part-{index}.mp4';parts.append(path)
                with av.open(str(path),'w') as output:
                    stream=output.add_stream('libx264',rate=25)
                    stream.width,stream.height,stream.pix_fmt=64,48,'yuv420p'
                    for i in range(5):
                        image=av.VideoFrame.from_ndarray(np.full((48,64,3),index*80,np.uint8),format='rgb24')
                        for packet in stream.encode(image):output.mux(packet)
                    for packet in stream.encode():output.mux(packet)
            concatenate(parts,root/'full.mp4')
            with av.open(str(root/'full.mp4')) as result:
                stream=result.streams.video[0];frames=list(result.decode(stream))
                self.assertEqual(len(frames),10)
                self.assertEqual(float(stream.average_rate),25.)
                timestamps=[float(f.pts*f.time_base) for f in frames]
                self.assertEqual([round(t*25) for t in timestamps],list(range(10)))
