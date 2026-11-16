"""Deterministic 60fps soundtrack and actual-image evidence integration."""
import sys,tempfile,hashlib,json,subprocess,unittest,wave
from pathlib import Path
try:
    import numpy as np
    import cv2
except ImportError:
    np=cv2=None
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from git_evidence import commit_from_git,validate_commit,annotate_session

class ThreeLayerTests(unittest.TestCase):
    def test_git_commit_and_private_diff_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            subprocess.run(['git','init','-q',str(root)],check=True)
            subprocess.run(['git','-C',str(root),'config','user.email','test@example.org'],check=True)
            subprocess.run(['git','-C',str(root),'config','user.name','Test'],check=True)
            file=root/'feature.ts';file.write_text('export const feature = false;\n')
            subprocess.run(['git','-C',str(root),'add','feature.ts'],check=True)
            subprocess.run(['git','-C',str(root),'commit','-qm','Initial feature'],check=True)
            file.write_text('export const feature = true;\n')
            subprocess.run(['git','-C',str(root),'commit','-qam','Activate feature'],check=True)
            sha=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
            evidence=commit_from_git(root,sha)
            self.assertEqual(evidence['sha'],sha)
            self.assertTrue(any('feature = true' in l for l in evidence['lines']))
            with self.assertRaisesRegex(ValueError,'Unsafe'):
                validate_commit({**evidence,'lines':['+const api_key = "secret";']})
            with self.assertRaises(ValueError):commit_from_git(root,'--evil')

    @unittest.skipUnless(cv2 is not None,'Requires render extras')
    def test_saliency_comes_from_hash_checked_source_frames(self):
        from spatial_parallax import evidence_attention_events
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'states').mkdir()
            states=[]
            for i in range(2):
                image=np.zeros((360,640,3),np.uint8)
                cv2.rectangle(image,(75+i*175,75),(260+i*175,260),(240,240,240),-1)
                path=root/'states'/f'{i}.png';cv2.imwrite(str(path),image)
                states.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                               'at_ms':i*900})
            session={'page':{'viewport':[1280,720]},'states':states}
            proposal=evidence_attention_events(root,session)
            self.assertTrue(proposal)
            self.assertTrue(all(0<=e['x']<=1280 and 0<=e['y']<=720 for e in proposal))
            states[1]['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'hash'):
                evidence_attention_events(root,session)

    @unittest.skipUnless(np is not None,'Requires render extras')
    def test_foley_shader_uniforms_sample_locked_and_muted(self):
        from foley_mixer import foley_shader_envelopes,render_foley_plan
        plan={'schema':'sauce-foley-plan-v1','sampleRate':48000,'durationMs':1000,
              'muted':False,'masterGain':.6,'musicGain':0,
              'cues':[{'sound':'click_crisp','outputSample':800,'gain':.7,
                       'outputMs':800/48,'sourceMs':800/48},
                      {'sound':'pop_glass','outputSample':4800,'gain':.7,
                       'outputMs':4800/48,'sourceMs':4800/48}],
              'duckIntervals':[]}
        uniforms=foley_shader_envelopes(plan,60)
        self.assertEqual((len(uniforms['click']),len(uniforms['glass'])),(60,60))
        self.assertEqual(uniforms['click'][0],0.)
        self.assertGreater(uniforms['click'][1],0.)
        self.assertEqual(uniforms['glass'][1],0.)
        self.assertGreater(uniforms['glass'][6],0.)
        self.assertEqual(foley_shader_envelopes({**plan,'muted':True},60),
                         {'click':[0.]*60,'glass':[0.]*60})
        with tempfile.TemporaryDirectory() as d:
            result=render_foley_plan(plan,Path(d)/'audio.wav',target_duration_ms=1000)
            with wave.open(str(Path(d)/'audio.wav')) as wav:
                self.assertEqual(wav.getnframes(),60*800)
                self.assertEqual(wav.getframerate(),48000)
            self.assertEqual(result['cue_count'],2)

    @unittest.skipUnless(np is not None and cv2 is not None,'Requires render extras')
    def test_code_diff_is_real_overlay_and_source_frame_unchanged(self):
        from code_diff_reveal import compose_diff,peel_browser_frame
        frame=np.full((1080,1920,3),25,np.uint8)
        original=frame.copy()
        record={'sha':'abc1234','file':'feature.ts','title':'Add feature',
                'lines':['@@ -1 +1 @@','-const value = 1;','+const value = 2;']}
        compose_diff(frame,record,.85)
        self.assertTrue(np.array_equal(frame[30:100,30:100],original[30:100,30:100]))
        self.assertGreater(np.count_nonzero(frame!=original),300)
        with self.assertRaises(ValueError):compose_diff(original,record,1.4)
        surface=np.zeros((1080,1920,3),np.uint8)
        surface[124:956,220:1700]=180
        mask=np.zeros((1080,1920),np.float32)
        mask[124:956,220:1700]=1.
        scene=peel_browser_frame(surface,np.full_like(surface,12),record,1.,mask)
        self.assertGreater(int(scene[420,240,0]),120)
        self.assertLess(int(scene[420,1500,0]),100)
        self.assertFalse(np.array_equal(scene,surface))

if __name__=='__main__':unittest.main()
