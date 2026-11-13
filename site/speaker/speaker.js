(()=>{'use strict';
const $=id=>document.getElementById(id),data=JSON.parse($('manuscript-data').textContent),articles=[...document.querySelectorAll('.script-page')],links=[...document.querySelectorAll('a[data-page]')],groups=[...document.querySelectorAll('.nav-chapter')];
let current=1,mode='page',font=19,noticeTimer;
document.body.classList.add('js-ready','mode-page');
function hashPage(){const m=location.hash.match(/^#page-(\d+)$/);return m?Number(m[1]):1}
function closeMenu(){$('rail').classList.remove('open');$('mobile-menu').setAttribute('aria-expanded','false')}
function setPage(number,{scroll=false,hash=true}={}){
 current=Math.max(1,Math.min(data.length,Number.isFinite(number)?Math.trunc(number):1));
 if($('query').value){$('query').value='';filter()}
 for(const a of articles)a.classList.toggle('is-current',Number(a.dataset.page)===current);
 for(const a of links){if(Number(a.dataset.page)===current)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')}
 const active=links.find(a=>Number(a.dataset.page)===current);if(active)active.closest('details').open=true;
 $('pages').value=String(current);$('counter').textContent=current+' / '+data.length;$('prev').disabled=current===1;$('next').disabled=current===data.length;
 $('preview-link').href='../preview/#page='+current;document.title=current+'/'+data.length+' · '+data[current-1].title+' · 逐页讲稿';
 if(hash)history.replaceState(null,'','#page-'+current);
 closeMenu();if(scroll)requestAnimationFrame(()=>articles[current-1].scrollIntoView({block:'start',behavior:'instant'}));
}
function filter(){const q=$('query').value.trim().toLocaleLowerCase();let count=0;
 for(const a of links){const match=!q||data[Number(a.dataset.page)-1].search.toLocaleLowerCase().includes(q);a.hidden=!match;if(match)count++}
 for(const g of groups){g.hidden=![...g.querySelectorAll('a[data-page]')].some(a=>!a.hidden);if(q&&!g.hidden)g.open=true}
 $('search-status').textContent=q?count+' 页匹配，点击目录定位':data.length+' 页可查阅';$('empty').hidden=count>0;
 if(mode==='all')for(const a of articles)a.hidden=!!q&&!data[Number(a.dataset.page)-1].search.toLocaleLowerCase().includes(q);
 else for(const a of articles)a.hidden=false;
}
function setMode(value){mode=value;for(const m of ['page','all','cue'])document.body.classList.toggle('mode-'+m,m===mode);filter();if(mode!=='all')setPage(current,{scroll:true});}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>$('toast').hidden=true,2400)}
links.forEach(a=>a.addEventListener('click',e=>{e.preventDefault();setPage(Number(a.dataset.page),{scroll:true})}));
$('prev').addEventListener('click',()=>setPage(current-1,{scroll:true}));$('next').addEventListener('click',()=>setPage(current+1,{scroll:true}));$('pages').addEventListener('change',()=>setPage(Number($('pages').value),{scroll:true}));
$('mode').addEventListener('change',()=>setMode($('mode').value));$('query').addEventListener('input',filter);
$('mobile-menu').addEventListener('click',()=>{const open=$('rail').classList.toggle('open');$('mobile-menu').setAttribute('aria-expanded',String(open))});
$('larger').addEventListener('click',()=>{font=Math.min(29,font+1);document.documentElement.style.setProperty('--speech-size',font+'px')});$('smaller').addEventListener('click',()=>{font=Math.max(16,font-1);document.documentElement.style.setProperty('--speech-size',font+'px')});
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',async()=>{const d=data[Number(b.dataset.copy)-1],text='第'+d.page+'页　'+d.title+'\n\n'+d.speech.join('\n\n')+'\n\n'+d.transition;
 try{if(!navigator.clipboard)throw new Error('clipboard unavailable');await navigator.clipboard.writeText(text);toast('已复制本页讲稿')}
 catch{$('copy-text').value=text;$('copy-dialog').showModal();$('copy-text').focus();$('copy-text').select()}
}));
$('print').addEventListener('click',async()=>{const button=$('print'),label=button.textContent;button.disabled=true;button.textContent='准备打印…';const images=[...document.querySelectorAll('.slide-figure img')];for(const img of images)img.loading='eager';try{await Promise.race([Promise.all(images.map(img=>img.decode().catch(()=>{}))),new Promise(resolve=>setTimeout(resolve,15000))]);window.print()}finally{button.disabled=false;button.textContent=label}});
window.addEventListener('beforeprint',()=>{for(const img of document.querySelectorAll('.slide-figure img'))img.loading='eager'});
window.addEventListener('hashchange',()=>setPage(hashPage(),{scroll:true,hash:false}));
document.addEventListener('keydown',e=>{if(e.altKey||e.ctrlKey||e.metaKey||e.target.closest('input,select,textarea,button,summary,dialog')||mode==='all')return;let target=null;if(e.key==='ArrowRight')target=current+1;if(e.key==='ArrowLeft')target=current-1;if(e.key==='Home')target=1;if(e.key==='End')target=data.length;if(target!==null){e.preventDefault();setPage(target,{scroll:true})}});
setPage(hashPage(),{scroll:!!location.hash,hash:false});
})();
