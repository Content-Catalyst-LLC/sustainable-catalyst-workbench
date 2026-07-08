from __future__ import annotations
import math
import re
from typing import Any
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from .common import parse_number_list, parse_rows, parse_kv, result, svg_from_figure, bar_graph

NOTE_NAMES_SHARP = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
NOTE_TO_PC = {n:i for i,n in enumerate(NOTE_NAMES_SHARP)}
NOTE_TO_PC.update({'Db':1,'Eb':3,'Gb':6,'Ab':8,'Bb':10,'Cb':11,'B#':0,'E#':5,'Fb':4})
MAJOR = [0,2,4,5,7,9,11]
NAT_MINOR = [0,2,3,5,7,8,10]
MODES = {
    'ionian/major':[0,2,4,5,7,9,11],
    'dorian':[0,2,3,5,7,9,10],
    'phrygian':[0,1,3,5,7,8,10],
    'lydian':[0,2,4,6,7,9,11],
    'mixolydian':[0,2,4,5,7,9,10],
    'aeolian/natural minor':[0,2,3,5,7,8,10],
    'locrian':[0,1,3,5,6,8,10],
}
CHORDS = {
    'major triad':[0,4,7], 'minor triad':[0,3,7], 'diminished triad':[0,3,6], 'augmented triad':[0,4,8],
    'dominant seventh':[0,4,7,10], 'major seventh':[0,4,7,11], 'minor seventh':[0,3,7,10], 'half-diminished seventh':[0,3,6,10]
}

def _note_to_midi(note: str) -> int:
    note = str(note).strip()
    m = re.match(r'^([A-Ga-g])([#b]?)(-?\d+)$', note)
    if not m:
        # allow raw midi
        return int(float(note))
    name = m.group(1).upper() + m.group(2)
    octave = int(m.group(3))
    return 12 * (octave + 1) + NOTE_TO_PC[name]

def _pc_name(pc: int) -> str:
    return NOTE_NAMES_SHARP[int(pc) % 12]

def music_frequency_calculator(inputs: dict[str, Any]):
    mode = inputs.get('mode') or 'midi_to_frequency'
    graphs=[]
    if mode == 'equal_temperament':
        f0=float(inputs.get('f0', 440)); steps=int(float(inputs.get('steps', 12))); n=np.arange(0, steps+1); freqs=f0*(2**(n/12))
        values={'base_frequency':f0,'steps':steps,'final_frequency':float(freqs[-1]),'frequencies':freqs.round(4).tolist()}
        graphs.append(bar_graph([str(i) for i in n], freqs.tolist(), 'Equal-temperament frequencies', 'Hz'))
    elif mode == 'cents_between':
        f1=float(inputs.get('f1', 440)); f2=float(inputs.get('f2', 466.1638)); cents=1200*math.log2(f2/f1); values={'frequency_1':f1,'frequency_2':f2,'ratio':f2/f1,'cents':cents,'beat_frequency_hz':abs(f2-f1)}
        graphs.append(bar_graph(['f1','f2','beat Hz'], [f1,f2,abs(f2-f1)], 'Frequency comparison', 'Hz'))
    elif mode == 'tempo':
        bpm=float(inputs.get('bpm', 120)); beats=np.arange(1,17); times=beats*60/bpm; values={'bpm':bpm,'seconds_per_beat':60/bpm,'bar_duration_4_4_seconds':4*60/bpm}
        fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.step(beats,times,where='post'); ax.set_title('Beat timing grid'); ax.set_xlabel('Beat'); ax.set_ylabel('Seconds'); ax.grid(alpha=.25); graphs.append({'title':'Beat timing','type':'step','svg':svg_from_figure(fig)}); plt.close(fig)
    elif mode == 'harmonic_series':
        fundamental=float(inputs.get('fundamental',110)); partials=int(float(inputs.get('partials',16))); n=np.arange(1,partials+1); freqs=fundamental*n; values={'fundamental':fundamental,'partials':partials,'frequencies':freqs.tolist()}
        graphs.append(bar_graph([str(i) for i in n], freqs.tolist(), 'Harmonic series', 'Hz'))
    else:
        midi=float(inputs.get('midi', 69)); frequency=440*(2**((midi-69)/12)); values={'midi':midi,'frequency_hz':frequency,'nearest_note':_pc_name(int(round(midi)) % 12)}
        around=np.arange(int(midi)-12,int(midi)+13); freqs=440*(2**((around-69)/12)); fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(around,freqs); ax.scatter([midi],[frequency]); ax.set_title('MIDI to frequency curve'); ax.set_xlabel('MIDI note'); ax.set_ylabel('Hz'); ax.grid(alpha=.25); graphs.append({'title':'MIDI frequency curve','type':'curve','svg':svg_from_figure(fig)}); plt.close(fig)
    return result('Music Frequency Calculator', f'Ran music mode: {mode}.', values, [], graphs, ['Apply equal-temperament, MIDI, cents, harmonic, or tempo formulas', 'Render frequency or timing relationship'], 'python/numpy')


def chord_scale_identifier(inputs: dict[str, Any]):
    notes_text = inputs.get('notes','C E G')
    tokens = [t.strip().replace('♯','#').replace('♭','b') for t in re.split(r'[\s,;]+', str(notes_text)) if t.strip()]
    pcs = sorted({NOTE_TO_PC.get(t[:-1] if re.match(r'^[A-Ga-g][#b]?-?\d+$', t) else t[0].upper()+t[1:].replace('B','b'), None) if not re.match(r'^-?\d+$', t) else int(t)%12 for t in tokens})
    pcs = [p for p in pcs if p is not None]
    if not pcs: raise ValueError('Enter note names such as C E G or MIDI pitch classes such as 0 4 7.')
    chord_matches=[]
    scale_matches=[]
    for root in range(12):
        rel=sorted(((p-root)%12 for p in pcs))
        for name, pattern in CHORDS.items():
            if rel == pattern:
                chord_matches.append(f'{_pc_name(root)} {name}')
        for name, pattern in MODES.items():
            if all(r in pattern for r in rel):
                scale_matches.append(f'{_pc_name(root)} {name}')
    values={'pitch_classes':pcs,'note_names':[_pc_name(p) for p in pcs],'chord_matches':chord_matches[:10] or ['no exact common chord match'], 'scale_candidates':scale_matches[:12]}
    graph=bar_graph([_pc_name(i) for i in range(12)], [1 if i in pcs else 0 for i in range(12)], 'Pitch-class set', 'Present')
    return result('Chord and Scale Identifier', 'Identified pitch classes and matched common chord/scale patterns.', values, [], [graph], ['Normalize note names', 'Compare pitch-class set to chord templates', 'Find scale candidates'], 'python')


def _hex_to_rgb(h: str):
    h=str(h).strip().lstrip('#')
    if len(h)==3: h=''.join(c*2 for c in h)
    if len(h)!=6: raise ValueError('Color must be HEX such as #ff0000.')
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def _rgb_to_hex(rgb):
    return '#' + ''.join(f'{max(0,min(255,int(round(c)))):02x}' for c in rgb)

def _srgb_channel(c):
    c=c/255
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4

def _luminance(rgb):
    r,g,b=(_srgb_channel(c) for c in rgb)
    return 0.2126*r + 0.7152*g + 0.0722*b

def color_contrast_calculator(inputs: dict[str, Any]):
    fg=_hex_to_rgb(inputs.get('foreground','#111111')); bg=_hex_to_rgb(inputs.get('background','#fff8e7'))
    L1,L2=sorted([_luminance(fg),_luminance(bg)], reverse=True); contrast=(L1+0.05)/(L2+0.05)
    dist=math.sqrt(sum((fg[i]-bg[i])**2 for i in range(3)))
    values={'foreground_rgb':fg,'background_rgb':bg,'relative_luminance_foreground':_luminance(fg),'relative_luminance_background':_luminance(bg),'contrast_ratio':contrast,'wcag_aa_normal':contrast>=4.5,'wcag_aa_large':contrast>=3,'rgb_distance':dist}
    graph=bar_graph(['L foreground','L background','contrast'], [_luminance(fg),_luminance(bg),contrast], 'Color contrast analytics')
    return result('Color Contrast and Luminance Calculator', 'Computed relative luminance, contrast ratio, accessibility flags, and color distance.', values, [], [graph], ['Convert HEX to RGB', 'Linearize sRGB', 'Compute relative luminance and contrast'], 'python')


def color_harmony_generator(inputs: dict[str, Any]):
    import colorsys
    base=_hex_to_rgb(inputs.get('base','#ff0000'))
    h,l,s = colorsys.rgb_to_hls(*(c/255 for c in base))
    def rgb_at(delta):
        r,g,b=colorsys.hls_to_rgb((h+delta)%1,l,s); return _rgb_to_hex((r*255,g*255,b*255))
    palette={'base':_rgb_to_hex(base),'complementary':rgb_at(.5),'analogous_minus':rgb_at(-1/12),'analogous_plus':rgb_at(1/12),'triadic_1':rgb_at(1/3),'triadic_2':rgb_at(2/3)}
    labels=list(palette.keys()); vals=[]
    for hx in palette.values():
        vals.append(_luminance(_hex_to_rgb(hx)))
    graph=bar_graph(labels, vals, 'Palette luminance profile', 'Relative luminance')
    return result('Color Harmony Generator', 'Generated complementary, analogous, and triadic palette relationships.', {'palette':palette,'base_hue_degrees':h*360,'lightness':l,'saturation':s}, [], [graph], ['Convert to HLS', 'Rotate hue for harmony relationships', 'Return palette and luminance profile'], 'python')


def vector_geometry_calculator(inputs: dict[str, Any]):
    mode=inputs.get('mode') or 'dot_angle_projection'
    a=np.array(parse_number_list(inputs.get('a','1,2,3')), dtype=float)
    b=np.array(parse_number_list(inputs.get('b','4,5,6')), dtype=float)
    if a.size != b.size: raise ValueError('Vectors a and b must have the same dimension.')
    dot=float(np.dot(a,b)); na=float(np.linalg.norm(a)); nb=float(np.linalg.norm(b)); cos=dot/(na*nb) if na and nb else float('nan'); angle=math.degrees(math.acos(max(-1,min(1,cos)))) if np.isfinite(cos) else None
    values={'dimension':int(a.size),'dot_product':dot,'norm_a':na,'norm_b':nb,'cosine_similarity':cos,'angle_degrees':angle,'distance':float(np.linalg.norm(a-b))}
    graphs=[]
    if mode == 'projection':
        proj=(dot/(nb**2))*b if nb else np.zeros_like(b); values['projection_of_a_onto_b']=proj.tolist(); graphs.append(bar_graph([f'd{i+1}' for i in range(a.size)], proj.tolist(), 'Projection components'))
    elif mode == 'cross_product' and a.size==3:
        values['cross_product']=np.cross(a,b).tolist(); graphs.append(bar_graph(['x','y','z'], values['cross_product'], 'Cross product components'))
    elif a.size==2:
        fig,ax=plt.subplots(figsize=(6,6)); ax.arrow(0,0,a[0],a[1],head_width=.08,length_includes_head=True,label='a'); ax.arrow(0,0,b[0],b[1],head_width=.08,length_includes_head=True,label='b'); lim=max(1,float(np.max(np.abs(np.r_[a,b]))))*1.25; ax.set_xlim(-lim,lim); ax.set_ylim(-lim,lim); ax.axhline(0,linewidth=1); ax.axvline(0,linewidth=1); ax.set_aspect('equal'); ax.set_title('2D vector geometry'); ax.grid(alpha=.25); graphs.append({'title':'Vector geometry','type':'vector','svg':svg_from_figure(fig)}); plt.close(fig)
    else:
        graphs.append(bar_graph(['dot','||a||','||b||','distance'], [dot,na,nb,values['distance']], 'Vector summary'))
    return result('Vector Geometry Calculator', f'Ran vector mode: {mode}.', values, [], graphs, ['Parse vectors', 'Compute norm, dot product, angle, distance, projection or cross product'], 'python/numpy')


def embedding_similarity_tool(inputs: dict[str, Any]):
    a=np.array(parse_number_list(inputs.get('a','0.2,0.1,0.9,0.4')), dtype=float)
    b=np.array(parse_number_list(inputs.get('b','0.1,0.3,0.8,0.5')), dtype=float)
    if a.size != b.size: raise ValueError('Embedding vectors must have same length.')
    dot=float(np.dot(a,b)); cos=dot/(np.linalg.norm(a)*np.linalg.norm(b)); euc=float(np.linalg.norm(a-b)); man=float(np.abs(a-b).sum())
    fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(a,label='embedding a'); ax.plot(b,label='embedding b'); ax.set_title('Embedding component comparison'); ax.legend(); ax.grid(alpha=.25); graph={'title':'Embedding comparison','type':'line','svg':svg_from_figure(fig)}; plt.close(fig)
    return result('Embedding Similarity Tool', 'Computed cosine similarity, Euclidean distance, Manhattan distance, and component comparison.', {'dimension':int(a.size),'cosine_similarity':float(cos),'dot_product':dot,'euclidean_distance':euc,'manhattan_distance':man}, [], [graph], ['Parse embedding vectors', 'Compute vector similarity and distances', 'Graph component profile'], 'python/numpy')


def pca_dimensionality_explorer(inputs: dict[str, Any]):
    X=parse_rows(inputs.get('data','1,2,3\n2,3,4\n3,4,6\n4,5,8\n5,7,10'))
    if X.ndim!=2 or X.shape[0]<2 or X.shape[1]<2: raise ValueError('Enter a numeric matrix with at least 2 rows and 2 columns.')
    Xc=X-X.mean(axis=0); U,S,Vt=np.linalg.svd(Xc, full_matrices=False); explained=(S**2)/(X.shape[0]-1); ratio=explained/explained.sum() if explained.sum() else explained
    scores=U*S
    fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.bar(range(1,len(ratio)+1),ratio); ax.set_title('PCA explained variance ratio'); ax.set_xlabel('Component'); ax.set_ylabel('Share'); ax.grid(axis='y',alpha=.25); graph1={'title':'Explained variance','type':'bar','svg':svg_from_figure(fig)}; plt.close(fig)
    graphs=[graph1]
    if scores.shape[1]>=2:
        fig,ax=plt.subplots(figsize=(6,5)); ax.scatter(scores[:,0], scores[:,1]); ax.axhline(0,linewidth=1); ax.axvline(0,linewidth=1); ax.set_title('PCA score plot'); ax.set_xlabel('PC1'); ax.set_ylabel('PC2'); ax.grid(alpha=.25); graphs.append({'title':'PCA scores','type':'scatter','svg':svg_from_figure(fig)}); plt.close(fig)
    return result('PCA / Dimensionality Reduction Explorer', 'Computed SVD-based PCA, explained variance, component loadings, and score plot.', {'shape':list(X.shape),'explained_variance_ratio':ratio.tolist(),'components':Vt.tolist()}, [], graphs, ['Center matrix', 'Run SVD', 'Compute explained variance', 'Render component diagnostics'], 'python/numpy')


def fourier_frequency_analysis(inputs: dict[str, Any]):
    data=np.array(parse_number_list(inputs.get('data','0,1,0,-1,0,1,0,-1,0,1,0,-1')), dtype=float)
    sample_rate=float(inputs.get('sample_rate',1))
    if data.size<4: raise ValueError('Enter at least four samples.')
    freqs=np.fft.rfftfreq(data.size, d=1/sample_rate); amps=np.abs(np.fft.rfft(data))/data.size; peak_idx=int(np.argmax(amps[1:])+1) if amps.size>1 else 0
    fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(freqs,amps); ax.set_title('Frequency spectrum'); ax.set_xlabel('Frequency'); ax.set_ylabel('Amplitude'); ax.grid(alpha=.25); graph={'title':'Fourier spectrum','type':'spectrum','svg':svg_from_figure(fig)}; plt.close(fig)
    return result('Fourier / Frequency Analysis Tool', 'Computed a discrete Fourier spectrum and identified the strongest nonzero frequency component.', {'n_samples':int(data.size),'sample_rate':sample_rate,'peak_frequency':float(freqs[peak_idx]),'peak_amplitude':float(amps[peak_idx])}, [], [graph], ['Parse signal samples', 'Compute real FFT', 'Plot amplitude spectrum'], 'python/numpy')


def ai_classification_metrics(inputs: dict[str, Any]):
    tp=float(inputs.get('tp',50)); fp=float(inputs.get('fp',10)); tn=float(inputs.get('tn',80)); fn=float(inputs.get('fn',5))
    acc=(tp+tn)/max(tp+tn+fp+fn,1); precision=tp/max(tp+fp,1); recall=tp/max(tp+fn,1); specificity=tn/max(tn+fp,1); f1=2*precision*recall/max(precision+recall,1e-12)
    graph=bar_graph(['accuracy','precision','recall','specificity','F1'], [acc,precision,recall,specificity,f1], 'Classification metrics')
    fig,ax=plt.subplots(figsize=(4.8,4.2)); im=ax.imshow([[tn,fp],[fn,tp]]); ax.set_xticks([0,1],['pred 0','pred 1']); ax.set_yticks([0,1],['true 0','true 1']); ax.set_title('Confusion matrix');
    for (i,j),v in np.ndenumerate(np.array([[tn,fp],[fn,tp]])): ax.text(j,i,int(v),ha='center',va='center')
    graphs=[graph, {'title':'Confusion matrix','type':'heatmap','svg':svg_from_figure(fig)}]; plt.close(fig)
    return result('AI Classification Metrics Calculator', 'Computed accuracy, precision, recall, specificity, F1, and confusion-matrix visualization.', {'accuracy':acc,'precision':precision,'recall':recall,'specificity':specificity,'f1':f1,'confusion_matrix':{'tn':tn,'fp':fp,'fn':fn,'tp':tp}}, [], graphs, ['Read confusion matrix counts', 'Compute core classification metrics', 'Render metrics and matrix'], 'python')


def multimodal_pattern_comparison(inputs: dict[str, Any]):
    a=np.array(parse_number_list(inputs.get('pattern_a','1,3,2,5,4,6')), dtype=float)
    b=np.array(parse_number_list(inputs.get('pattern_b','2,4,3,6,5,7')), dtype=float)
    if a.size != b.size: raise ValueError('Pattern vectors must have the same length.')
    za=(a-a.mean())/(a.std() or 1); zb=(b-b.mean())/(b.std() or 1); corr=float(np.corrcoef(a,b)[0,1]) if a.size>1 else 1.0; cos=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)))
    fig,ax=plt.subplots(figsize=(7.2,4.4)); ax.plot(a,label='pattern A'); ax.plot(b,label='pattern B'); ax.set_title('Pattern comparison'); ax.legend(); ax.grid(alpha=.25); graph={'title':'Pattern comparison','type':'line','svg':svg_from_figure(fig)}; plt.close(fig)
    return result('Multimodal Pattern Comparison Tool', 'Compared numeric pattern representations using correlation, cosine similarity, normalized distance, and profile graph.', {'length':int(a.size),'correlation':corr,'cosine_similarity':cos,'z_normalized_distance':float(np.linalg.norm(za-zb)),'euclidean_distance':float(np.linalg.norm(a-b))}, [], [graph], ['Parse pattern vectors', 'Normalize and compare profiles', 'Compute similarity and distance metrics'], 'python/numpy')
