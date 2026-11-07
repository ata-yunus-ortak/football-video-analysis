/* Same-source ground-plane points. No detector, identity assignment or offset tuning. */
(()=>{
 'use strict';
 function contain(point, iw, ih, cw, ch){
  if(!point||point.length!==2||!point.every(Number.isFinite)||![iw,ih,cw,ch].every(v=>Number.isFinite(v)&&v>0)
     ||point[0]<0||point[1]<0||point[0]>=iw||point[1]>=ih)return null;
  const scale=Math.min(cw/iw,ch/ih);
  return [(cw-iw*scale)/2+point[0]*scale,(ch-ih*scale)/2+point[1]*scale];
 }
 window.TrackingProjectionMath={contain};
 if(typeof document==='undefined')return;
 const layer=document.getElementById('tracking-overlay'),context=layer.getContext('2d'),stage=document.getElementById('video-stage');
 const label=document.getElementById('projection-status'),enabled=document.getElementById('project-tracking');
 let presented=-1,bound=false;
 function clear(){context.clearRect(0,0,layer.width,layer.height)}
 function draw(){
  clear();if(!meta)return;
  const audit=meta.clock_audit;
  if(!enabled.checked){label.textContent='Tracking izdüşümü kapalı.';return}
  if(!audit?.structural_clock_compatible||!meta.homography?.available){label.textContent='İzdüşüm kapalı: kaynağa bağlı saat denetimi veya homografi eksik/uyumsuz.';return}
  if(!video.requestVideoFrameCallback){label.textContent='Tarayıcı sunulan video karesini bildirmiyor; eski kareye işaret çizilmez.';return}
  if(!bound||!readyVideo||!document.getElementById('sync').checked){label.textContent='İzdüşüm yalnız denetlenen yerel video ve “Videoyla eşle” açıkken gösterilir.';return}
  if(video.seeking||presented<0||presented!==current||rowsFrame!==presented||presented>=audit.common_frames){label.textContent='Görüntü karesi ve aynı karenin tracking kaydı bekleniyor…';return}
  const index=Math.floor(presented/chunkSize),offset=presented%chunkSize;
  const sample=projectionChunks.get(index)?.[offset],geometry=geometryChunks.get(index)?.[offset];
  if(!sample||!geometry?.usable){label.textContent='Bu karede geçerli homografi yok; işaretler gizlendi.';return}
  if(sample.source_frame!==presented||sample.homography_frame!==presented||sample.atd_record!==presented+1){label.textContent='Kare kimlikleri uyuşmadı; işaretler gizlendi.';return}
  const dpr=devicePixelRatio||1;let count=0;
  sample.players_px.forEach((point,i)=>{
   const p=contain(point,video.videoWidth,video.videoHeight,layer.width,layer.height);if(!p)return;
   const object=meta.objects[i];if(!object||object.team<0)return;
   const color=colors[object.team],radius=(i===selected?8:5)*dpr;
   context.beginPath();context.arc(p[0],p[1],radius,0,Math.PI*2);context.fillStyle=color;context.fill();context.lineWidth=2*dpr;context.strokeStyle=i===selected?'white':'#11202b';context.stroke();
   context.font=`600 ${12*dpr}px system-ui`;context.textAlign='left';context.textBaseline='bottom';context.lineWidth=3*dpr;context.strokeStyle='#10151d';context.strokeText(String(object.id),p[0]+8*dpr,p[1]-4*dpr);context.fillStyle=color;context.fillText(String(object.id),p[0]+8*dpr,p[1]-4*dpr);count++;
  });
  label.textContent=`Video ${presented} → ATD ${presented+1} → H ${presented}: ${count} tracking noktası. Numaralar takip yuvasıdır. Zemin izdüşümü; kutu/kimlik doğrulaması yapılmadı.`;
 }
 function resize(){const dpr=devicePixelRatio||1;layer.width=Math.round(stage.clientWidth*dpr);layer.height=Math.round(stage.clientHeight*dpr);draw()}
 window.trackingProjection={draw,clear,usesPresentedFrames:!!video.requestVideoFrameCallback};
 if(video.requestVideoFrameCallback){
  const observe=(_,info)=>{if(meta){presented=Math.floor(info.mediaTime*meta.fps+1e-5);if(readyVideo&&document.getElementById('sync').checked&&presented>=0&&presented<=lastFrame()){if(current!==presented||rowsFrame!==presented)show(presented).catch(fail);else draw()}else clear()}video.requestVideoFrameCallback(observe)};
  video.requestVideoFrameCallback(observe);
 }
 video.addEventListener('loadedmetadata',()=>{const url=new URL(video.currentSrc||video.src,location.href);bound=url.origin===location.origin&&url.pathname==='/video';presented=-1;resize()});
 video.addEventListener('seeking',()=>{presented=-1;clear()});
 video.addEventListener('seeked',()=>{if(meta&&presented>=0&&document.getElementById('sync').checked)show(presented).catch(fail);else clear()});
 document.getElementById('video-file').addEventListener('change',()=>{bound=false;clear()});
 document.getElementById('sync').addEventListener('change',draw);enabled.addEventListener('change',draw);
 document.getElementById('objects').addEventListener('click',draw);document.getElementById('pitch').addEventListener('click',draw);
 new ResizeObserver(resize).observe(stage);resize();
})();
