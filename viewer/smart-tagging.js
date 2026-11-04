/* Read-only automatic tag browser. Never stores ratings, edits or match notes. */
(() => {
  const el = id => document.getElementById(id);
  const grid = document.querySelector('.grid'), tracking = grid.firstElementChild;
  const nav = document.createElement('nav');
  nav.className = 'view-nav'; nav.setAttribute('aria-label', 'Görünüm');
  nav.innerHTML = '<button id="view-tracking" aria-pressed="true">Tracking + video</button><button id="view-tags" aria-pressed="false">Smart Tagging + video</button><span id="tag-total" class="small muted">Olaylar yükleniyor…</span>';
  document.querySelector('header').after(nav);
  const panel = document.createElement('section');
  panel.className = 'panel'; panel.id = 'smart-panel'; panel.hidden = true;
  panel.innerHTML = `<div class="panel-head"><h2>Smart Tagging · tüm olaylar</h2><span id="tag-count" class="small muted"></span></div>
    <div class="tag-filters"><label class="tag-search">Ara<input id="tag-search" type="search" placeholder="Olay veya herhangi bir etiket…"></label>
    <label>Olay türü<select id="tag-code"><option value="">Tümü</option></select></label>
    <label>Takım<select id="tag-team"><option value="">Tümü</option></select></label>
    <label>Devre<select id="tag-half"><option value="">Tümü</option></select></label>
    <label>Alt tür<select id="tag-type"><option value="">Tümü</option></select></label></div>
    <div class="tag-options"><label><input id="tag-only-active" type="checkbox">Yalnız bu anda aktif</label><button id="tag-clear">Filtreleri temizle</button></div>
    <div id="tag-list" class="tag-list" role="list" aria-label="Otomatik olay listesi"></div>
    <div class="tag-selected"><div class="tag-selected-head"><h2 id="tag-selected-title">Bir olay seç</h2><span id="tag-selected-id" class="small muted"></span></div>
    <p id="tag-explanation" class="small muted">Orijinal XML alanlarını ve video aralığını burada görebilirsin.</p>
    <div id="tag-time" class="small"></div><div id="tag-fields" class="tag-fields"></div>
    <div class="tag-actions"><button id="tag-previous">← Önceki</button><button id="tag-play" class="primary">Aralığı oynat</button><button id="tag-next">Sonraki →</button><label><input id="tag-loop" type="checkbox">Aralığı tekrarla</label></div></div>`;
  grid.insertBefore(panel, tracking);
  const activePanel = document.createElement('div'); activePanel.className = 'tag-active-strip';
  activePanel.innerHTML = '<span class="small muted">Bu karedeki otomatik etiketler</span><div id="active-tags">Henüz yüklenmedi</div>';
  document.querySelector('.timeline').before(activePanel);
  const notice = document.createElement('p'); notice.className = 'notice';
  notice.textContent = 'Smart Tagging otomatik sağlayıcı yorumudur; kesin sahiplik veya doğruluk referansı değildir. Aralıklar oyun fazlarını gösterir ve üst üste binebilir. Bu ekran doğruluk puanı hesaplamaz, elle etiket/düzeltme kaydetmez.';
  panel.append(notice);
  const descriptions = {
    'BUILD UP': 'Geriden oyun kurma fazı. Tek bir kesintisiz sahiplik aralığı anlamına gelmez.',
    'PROGRESSION': 'Topu ilerletme fazına ilişkin otomatik yorum.',
    'SET PIECES': 'Duran top / yeniden başlama çevresindeki otomatik aralık. Kesin temas anı veya tüm duruş süresi değildir.',
    'ATTACKING TRANSITION': 'Hücuma geçiş fazına ilişkin otomatik yorum.',
    'DEFENSIVE TRANSITION': 'Savunmaya geçiş fazına ilişkin otomatik yorum.',
    'LONG BALL': 'Uzun top fazı / eylemine ilişkin otomatik yorum.',
    'GOALS': 'Gol olayının çevresindeki otomatik aralık.',
    'CREATING CHANCES': 'Pozisyon üretme fazına ilişkin otomatik yorum.',
    'BALL IN FINAL THIRD': 'Topun son üçte birlik bölgede bulunduğu otomatik faz.',
    'BALL IN THE BOX': 'Topun ceza alanında bulunduğu otomatik faz.',
    'PLAYERS IN THE BOX': 'Ceza alanındaki oyuncularla ilgili otomatik faz.',
    'DEFENDING IN MIDDLE THIRD': 'Orta bölgede savunma fazına ilişkin otomatik yorum.',
    'DEFENDING IN DEFENSIVE THIRD': 'Savunma bölgesindeki savunma fazına ilişkin otomatik yorum.',
    'DEFENDING IN ATTACKING THIRD': 'Ön bölgede savunma fazına ilişkin otomatik yorum.'
  };
  const fieldNames = {'Team':'Takım', 'Half':'Devre', 'Type':'Alt tür', 'Side':'Taraf', 'Direction of ball entry':'Top giriş yönü', 'Max Players in the box':'Ceza alanındaki azami oyuncu'};
  let data = null, filtered = [], selected = null, activeIds = '', playingInterval = false, suppressUntil = null;
  const time = n => `${n<0?'−':''}${Math.floor(Math.abs(n)/60).toString().padStart(2,'0')}:${(Math.abs(n)%60).toFixed(2).padStart(5,'0')}`;
  const values = (event, group) => Object.entries(event.tags).filter(([key])=>key.toLowerCase()===group.toLowerCase()).flatMap(([,v])=>v);
  function view(tags) {
    panel.hidden = !tags; tracking.hidden = tags;
    document.querySelector('.bottom').hidden = tags;
    el('view-tags').setAttribute('aria-pressed', String(tags)); el('view-tracking').setAttribute('aria-pressed', String(!tags));
    if (!tags) window.dispatchEvent(new Event('resize'));
  }
  el('view-tags').onclick=()=>view(true); el('view-tracking').onclick=()=>view(false);
  function populate(id, options) {
    for (const value of [...new Set(options)].sort()) {
      const option=document.createElement('option');option.value=value;option.textContent=value||'(boş)';el(id).append(option);
    }
  }
  function active(event, frame) { return event.start_frame<=frame && frame<event.end_frame; }
  function renderList() {
    if(!data)return;
    const query=el('tag-search').value.trim().toLocaleLowerCase('tr');
    const frame=window.trackingViewer.getFrame();
    filtered=data.events.filter(event=> (!el('tag-code').value||event.code===el('tag-code').value)
      && (!el('tag-team').value||values(event,'Team').includes(el('tag-team').value))
      && (!el('tag-half').value||values(event,'Half').includes(el('tag-half').value))
      && (!el('tag-type').value||values(event,'Type').includes(el('tag-type').value))
      && (!el('tag-only-active').checked||active(event,frame))
      && (!query||[event.code,...Object.entries(event.tags).flatMap(([k,v])=>[k,...v])].join(' ').toLocaleLowerCase('tr').includes(query)));
    const list=el('tag-list');list.replaceChildren();
    el('tag-count').textContent=`${filtered.length} / ${data.count}`;
    if(!filtered.length){const p=document.createElement('p');p.className='muted';p.textContent='Bu filtrelerde olay yok.';list.append(p);}
    for(const event of filtered){const button=document.createElement('button');button.className='tag-event';button.dataset.eventId=event.id;button.setAttribute('role','listitem');
      button.setAttribute('aria-pressed',String(selected?.id===event.id));
      const title=document.createElement('strong');title.textContent=event.code;
      const sub=document.createElement('span');sub.textContent=`${time(event.start_s)}–${time(event.end_s)} · ${values(event,'Team').join(', ')||'Takım bilgisi yok'} · ${values(event,'Type').join(', ')||values(event,'Half').join(', ')}`;
      button.append(title,sub);button.onclick=()=>select(event,true);list.append(button);}
    paintActive(frame);updateNavigation();
  }
  function playable(){return selected&&selected.end_frame>Math.max(0,selected.start_frame)&&selected.start_frame<data.frame_count;}
  function updateNavigation(){const index=filtered.findIndex(e=>e.id===selected?.id);el('tag-previous').disabled=index<=0;el('tag-next').disabled=index<0||index>=filtered.length-1;el('tag-play').disabled=!playable();}
  function select(event, navigate) {
    selected=event;playingInterval=false;suppressUntil=null;
    el('tag-selected-title').textContent=event.code;
    el('tag-selected-id').textContent=`XML sıra ${event.id+1}${event.source_id?' · ID '+event.source_id:''}`;
    el('tag-explanation').textContent=descriptions[event.code]||'Sağlayıcının otomatik olay/faz etiketi. Alanlar orijinal XML değerleridir.';
    el('tag-time').textContent=`${time(event.start_s)} → ${time(event.end_s)} · ${event.duration_s.toFixed(2)} sn · kare [${event.start_frame}, ${event.end_frame})${event.outside_reference?' · video sınırı dışında değer var':''}`;
    const fields=el('tag-fields');fields.replaceChildren();
    for(const [group,vs] of Object.entries(event.tags)){const p=document.createElement('div'),label=document.createElement('span'),value=document.createElement('strong');label.textContent=(fieldNames[group]||group)+' · '+group;value.textContent=vs.join(' / ')||'(boş)';p.append(label,value);fields.append(p);}
    for(const extra of event.extras||[]){const p=document.createElement('div');p.textContent=extra.name+': '+extra.value;fields.append(p);}
    if(!Object.keys(event.tags).length){fields.textContent='Bu olayda ek etiket yok.';}
    for(const button of el('tag-list').querySelectorAll('.tag-event'))button.setAttribute('aria-pressed',String(+button.dataset.eventId===event.id));
    updateNavigation();if(navigate)window.trackingViewer.seek(event.start_frame);
  }
  function move(delta){const index=filtered.findIndex(e=>e.id===selected?.id),target=filtered[index+delta];if(target)select(target,true);}
  el('tag-previous').onclick=()=>move(-1);el('tag-next').onclick=()=>move(1);
  el('tag-play').onclick=()=>{if(!playable())return;window.trackingViewer.seek(selected.start_frame,{interval:true});playingInterval=true;suppressUntil=Math.max(0,selected.start_frame);window.trackingViewer.play();};
  function paintActive(frame){for(const button of el('tag-list').querySelectorAll('.tag-event')){const event=data.events.find(e=>e.id===+button.dataset.eventId);button.classList.toggle('is-current',active(event,frame));}}
  function onFrame(frame){if(!data)return;const events=data.events.filter(event=>active(event,frame)),key=events.map(e=>e.id).join(',');
    if(key!==activeIds){activeIds=key;const wrap=el('active-tags');wrap.replaceChildren();if(!events.length){wrap.textContent='Bu karede otomatik etiket yok.';}else for(const event of events){const button=document.createElement('button');button.textContent=event.code+' · '+(values(event,'Team').join(', ')||'—');button.onclick=()=>{view(true);select(event,false);};wrap.append(button);}
      if(el('tag-only-active').checked)renderList();else paintActive(frame);}
    if(playingInterval&&selected){if(suppressUntil!==null&&frame<suppressUntil)return;suppressUntil=null;
      if(frame>=Math.min(selected.end_frame,data.frame_count-1)){if(el('tag-loop').checked){window.trackingViewer.seek(selected.start_frame,{interval:true});suppressUntil=Math.max(0,selected.start_frame);window.trackingViewer.play();}
      else{playingInterval=false;window.trackingViewer.pause();window.trackingViewer.seek(Math.min(data.frame_count-1,selected.end_frame));}}}
  }
  for(const id of ['tag-search','tag-code','tag-team','tag-half','tag-type','tag-only-active'])el(id).addEventListener(id==='tag-search'?'input':'change',renderList);
  el('tag-clear').onclick=()=>{for(const id of ['tag-search','tag-code','tag-team','tag-half','tag-type'])el(id).value='';el('tag-only-active').checked=false;renderList();};
  document.addEventListener('tracking:frame',event=>onFrame(event.detail.frame));
  document.addEventListener('tracking:seek',event=>{if(!event.detail.interval){playingInterval=false;suppressUntil=null;}});
  fetch('/api/tags').then(response=>{if(!response.ok)throw Error('Smart Tagging yüklenemedi');return response.json();}).then(result=>{
    data=result;el('tag-total').textContent=result.available?`${result.count} otomatik olay · salt okunur`:'Smart Tagging dosyası bağlanmamış';
    populate('tag-code',result.events.map(e=>e.code));populate('tag-team',result.events.flatMap(e=>values(e,'Team')));populate('tag-half',result.events.flatMap(e=>values(e,'Half')));populate('tag-type',result.events.flatMap(e=>values(e,'Type')));
    renderList();if(result.events.length)select(result.events[0],false);activeIds='uninitialized';onFrame(window.trackingViewer.getFrame());
    if(location.hash==='#smart-tagging')view(true);
  }).catch(error=>{el('tag-total').textContent=error.message;});
})();
