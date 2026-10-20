/* Presentation / live GUI hand-off. No third-party scripts or saved passwords. */
(function(){
 'use strict';
 var first='250424_143312128093.jpg', second='250424_143017228317.jpg';
 var isGuiDeck=location.pathname.indexOf('/presentation/')===0;
 var base=location.protocol==='file:'?'http://localhost:8010/':isGuiDeck?new URL('/',location.href).href:new URL('/demo/',location.href).href;
 var launch=0, activeLink=null, dialog=document.createElement('dialog');
 dialog.id='live-dialog';dialog.setAttribute('aria-label','Final 모델 라이브 시연');
 dialog.innerHTML='<div class="live-dialog-bar"><button type="button" data-live-close>← 발표로 돌아가기</button><strong>Final Model · 검출 시연</strong><small>Esc로 복귀</small><a data-live-new target="_blank" rel="noopener">별도 탭 ↗</a></div><div class="live-dialog-error" role="status">시연 서버에 연결하지 못했습니다. GUI 서버가 실행 중인지 확인하거나 <button type="button" data-live-fallback>저장된 비교 사진</button>을 확인하세요.</div><iframe id="live-frame" title="Final 모델 검출 프로그램" allow="fullscreen"></iframe>';
 document.body.appendChild(dialog);
 var frame=dialog.querySelector('iframe'),err=dialog.querySelector('.live-dialog-error'),timer=null;
 function returnUrl(){var u=new URL(location.href);return u.href;}
 function urlFor(scene){var u=new URL(base);u.searchParams.set('embedded','1');u.searchParams.set('return',returnUrl());u.hash='img='+encodeURIComponent(scene==='threshold'?second:first)+'&mode='+(scene==='pred'?'pred':'cmp')+'&conf=0.25&scene='+encodeURIComponent(scene);return u;}
 function close(){clearTimeout(timer);if(dialog.open)dialog.close();document.body.classList.remove('live-open');if(activeLink)activeLink.focus();}
 function backups(){close();location.hash='16';document.getElementById('live-backups').classList.add('on');}
 function open(scene,trigger){activeLink=trigger;var u=urlFor(scene);u.searchParams.set("launch",String(++launch));err.classList.remove('on');dialog.querySelector('[data-live-new]').href=u.href;
   if(!dialog.open)dialog.showModal();document.body.classList.add('live-open');frame.src=u.href;
   clearTimeout(timer);timer=setTimeout(function(){err.classList.add('on');},15000);
 }
 document.querySelectorAll('[data-demo]').forEach(function(el){var u=urlFor(el.dataset.demo);if(el.tagName==='A')el.href=u.href;el.addEventListener('click',function(e){e.preventDefault();open(el.dataset.demo,el);});});
 document.querySelectorAll('[data-demo-standalone]').forEach(function(el){var u=urlFor('pred');u.searchParams.delete('embedded');el.href=u.href;});
 document.querySelectorAll('[data-show-backups]').forEach(function(el){el.onclick=function(){document.getElementById('live-backups').classList.add('on');};});
 document.querySelectorAll('[data-hide-backups]').forEach(function(el){el.onclick=function(){document.getElementById('live-backups').classList.remove('on');};});
 dialog.querySelector('[data-live-close]').onclick=close;dialog.querySelector('[data-live-fallback]').onclick=backups;
 dialog.addEventListener('cancel',function(e){e.preventDefault();close();});
 window.addEventListener('message',function(e){if(e.source!==frame.contentWindow||e.origin!==new URL(base).origin)return;
   if(e.data&&e.data.type==='g3-demo:ready'){clearTimeout(timer);err.classList.remove('on');}
   if(e.data&&e.data.type==='g3-demo:close')close();
 });
 window.addEventListener('keydown',function(e){if(dialog.open&&e.target!==frame){e.stopImmediatePropagation();if(e.key==='Escape'){e.preventDefault();close();}}},true);
 async function health(){var targets=document.querySelectorAll('[data-demo-status]');try{var r=await fetch(new URL('api/info',base),{signal:AbortSignal.timeout(3500)});if(!r.ok)throw Error();var info=await r.json();targets.forEach(function(el){el.dataset.state=info.ready?'ready':'loading';el.textContent=info.ready?'연결됨 · Final 모델 준비 완료':info.error?'모델 준비 오류 · 백업 사진 사용 가능':'연결됨 · 모델 준비 중';});}catch(e){targets.forEach(function(el){el.dataset.state='offline';el.textContent='서버 대기 중 · 저장된 비교 사진 사용 가능';});}}
 health();var slide=document.querySelector('#stage > [data-id="16"]');if(slide)new MutationObserver(function(){if(slide.classList.contains('active'))health();}).observe(slide,{attributes:true,attributeFilter:['class']});
})();