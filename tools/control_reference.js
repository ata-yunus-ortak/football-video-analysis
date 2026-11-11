"use strict";
const $=id=>document.getElementById(id);
const names={control_start:"Kontrol başlangıcı",control_end:"Kontrol bitişi",touch:"Temas",pass:"Pas",turnover:"Top kaybı",stop:"Oyun durdu",restart:"Oyun başladı"};
let current=0,events=[],coverage=[],serial=0;
const drafts=new Map();
const info=()=>window.REVIEW_PACK.clips[current];
const reviewed=()=>Object.keys(names).filter(k=>$("check_"+k).checked);
const now=()=>Math.round($("video").currentTime*info().fps)/info().fps;
function message(s){$("message").textContent=s;}
function list(id,rows,format){$(id).replaceChildren();rows.forEach((r,i)=>{const li=document.createElement("li");li.append(document.createTextNode(format(r)));const b=document.createElement("button");b.textContent="Sil";b.onclick=()=>{rows.splice(i,1);render();};li.append(b);$(id).append(li);});}
function render(){list("coverage",coverage,r=>`${r[0]}–${r[1]} s`);list("events",events,r=>`${names[r.kind]}: ${r.earliest_s}–${r.latest_s} s, ${r.team||"takım bilinmiyor"}`);}
function choose(){const saved=drafts.get(current);if(saved){events=saved.events;coverage=saved.coverage;serial=saved.serial;}else{events=[];coverage=[];serial=0;}
Object.keys(names).forEach(k=>$("check_"+k).checked=!!saved?.kinds.includes(k));$("attest").checked=false;
$("video").src=info().preview_file;$("coverageEnd").value=info().duration_s;$("split").textContent=`Maç ${info().game_id} · ${info().split} · ${info().fps} fps`;render();message("Taslak henüz kaydedilmedi. Sayfayı kapatmadan JSON indirin.");}
Object.entries(names).forEach(([k,v])=>{const label=document.createElement("label"),check=document.createElement("input");check.type="checkbox";check.id="check_"+k;label.append(check,document.createTextNode(v));$("kinds").append(label);const option=new Option(v,k);$("kind").add(option);});
window.REVIEW_PACK.clips.forEach((c,i)=>$("clip").add(new Option(c.sequence,String(i))));
$("clip").onchange=()=>{drafts.set(current,{events,coverage,serial,kinds:reviewed()});current=Number($("clip").value);choose();};
$("video").ontimeupdate=()=>$("clock").textContent=`${now().toFixed(2)} s · kare ${Math.round(now()*info().fps)}`;
$("rate").onchange=()=>$("video").playbackRate=Number($("rate").value);
function step(d){$("video").pause();$("video").currentTime=Math.max(0,Math.min(info().duration_s-1/info().fps,now()+d/info().fps));}
$("prev").onclick=()=>step(-1);$("next").onclick=()=>step(1);
$("setEarly").onclick=()=>$("earliest").value=now();$("setLate").onclick=()=>$("latest").value=now();
$("addCoverage").onclick=()=>{const a=Number($("coverageStart").value),b=Number($("coverageEnd").value);if(!Number.isFinite(a)||!Number.isFinite(b)||a<0||a>=b||b>info().duration_s||coverage.some(([x,y])=>a<y&&b>x)){message("Geçerli, çakışmayan ve video içinde bir kapsam girin.");return;}coverage.push([a,b]);coverage.sort((x,y)=>x[0]-y[0]);render();};
$("addEvent").onclick=()=>{const a=Number($("earliest").value),b=Number($("latest").value),kind=$("kind").value;if(!reviewed().includes(kind)||!Number.isFinite(a)||!Number.isFinite(b)||a>b||!coverage.some(([x,y])=>x<=a&&b<y)){message("Olay türünü incelenen kapsama seçin; olayın tamamı zaman kapsamının içinde olmalı.");return;}events.push({id:`event-${++serial}`,kind,earliest_s:a,latest_s:b,team:$("team").value||null,owner_id:$("owner").value.trim()||null});events.sort((a,b)=>a.earliest_s-b.earliest_s);render();};
$("export").onclick=()=>{const kinds=reviewed();if(!$("attest").checked||!coverage.length||!kinds.length||events.some(e=>!kinds.includes(e.kind)||!coverage.some(([a,b])=>a<=e.earliest_s&&e.latest_s<b))){message("Bağımsız incelemeyi onaylayın; kapsam, olay türleri ve olayları kontrol edin.");return;}
const c=info(),doc={provided_fixture_used:false,source_kind:"permitted_external_video",reference_origin:"external_human_review",game_id:c.game_id,split:c.split,video_sha256:c.video_sha256,preview_sha256:c.preview_sha256,reviewed_event_kinds:kinds,coverage_s:coverage,events,review_attestation:true};
const url=URL.createObjectURL(new Blob([JSON.stringify(doc,null,2)+"\n"],{type:"application/json"}));const a=document.createElement("a");a.href=url;a.download=c.sequence+"-reference.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),5000);message("JSON indirme başlatıldı. Dosyayı projedeki referans doğrulayıcıdan geçirin.");};
choose();
