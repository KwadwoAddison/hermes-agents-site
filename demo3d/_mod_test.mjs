
document.title='MODULE_RAN';
import * as THREE from 'three';
import { GLTFLoader } from './jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from './jsm/loaders/DRACOLoader.js';

const stage = document.getElementById('stage');
const renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
stage.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x0b0c0e, 0.028);
const camera = new THREE.PerspectiveCamera(38, innerWidth/innerHeight, .1, 200);

// lights (match the render's studio mood)
scene.add(new THREE.AmbientLight(0x334, 1.2));
const key = new THREE.DirectionalLight(0xfff2dc, 2.6); key.position.set(-8, 14, -6); scene.add(key);
const rim = new THREE.DirectionalLight(0xc49a4e, 2.2); rim.position.set(9, 6, 8); scene.add(rim);
const fill = new THREE.DirectionalLight(0x3fbdb8, .5); fill.position.set(0, -6, 6); scene.add(fill);

// sculpture group
const sculpture = new THREE.Group(); scene.add(sculpture);
const H = 33.67;            // tower height from build
const TOWER_MID = H/2;

// floor reflection fake: dark disc
const floor = new THREE.Mesh(
  new THREE.CircleGeometry(40, 48),
  new THREE.MeshStandardMaterial({color:0x08090b, roughness:.42, metalness:.55})
);
floor.rotation.x = -Math.PI/2; floor.position.y = -0.45; scene.add(floor);

// load GLB (DRACO)
const draco = new DRACOLoader();
draco.setDecoderPath('./draco/');
const loader = new GLTFLoader(); loader.setDRACOLoader(draco);
let ringsReady = false;
loader.load('./weight_of_276.glb', (gltf)=>{ document.title='LOADED';
  const model = gltf.scene;
  // center tower at origin, base at y=0
  const box = new THREE.Box3().setFromObject(model);
  model.position.y = -box.min.y;
  sculpture.add(model);
  ringsReady = true;
  document.getElementById('loadbar').style.width = '100%';
  setTimeout(()=>{ const l=document.getElementById('load'); l.style.opacity=0; setTimeout(()=>l.remove(), 900); }, 350);
}, (ev)=>{ if(ev.total) document.getElementById('loadbar').style.width = Math.round(ev.loaded/ev.total*90)+'%'; }, (err)=>{ document.title='LOADFAIL:'+String(err).slice(0,80); });

// ---- interaction state ----
const mouse = {x:0, y:0, tx:0, ty:0};
addEventListener('pointermove', e=>{
  mouse.tx = (e.clientX/innerWidth - .5)*2;
  mouse.ty = (e.clientY/innerHeight - .5)*2;
});

// scroll progress 0..1
let prog = 0;
function scrollProg(){
  const max = document.body.scrollHeight - innerHeight;
  prog = max>0 ? Math.min(1, scrollY/max) : 0;
}
addEventListener('scroll', scrollProg, {passive:true}); scrollProg();

function ease(t){ return t<.5 ? 2*t*t : 1-Math.pow(-2*t+2,2)/2; }

// count-up numbers when visible
const io = new IntersectionObserver(es=>{
  es.forEach(en=>{
    if(!en.isIntersecting) return;
    const el = en.target, target = +el.dataset.count, dur = 1400, t0 = performance.now();
    const tick = (t)=>{
      const k = Math.min(1,(t-t0)/dur), e = 1-Math.pow(1-k,3);
      el.textContent = Math.round(target*e);
      if(k<1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    io.unobserve(el);
  });
},{threshold:.6});
document.querySelectorAll('.num').forEach(n=>io.observe(n));

// ring highlight by chapter (41/178/96/2): pulse emissive on material groups is complex on one GLB;
// instead: chapter light follows the camera band of the tower
const chapLight = new THREE.PointLight(0xc49a4e, 40, 14, 2); scene.add(chapLight);

const clock = new THREE.Clock();
function tick(){
  requestAnimationFrame(tick);
  const dt = clock.getDelta();
  mouse.x += (mouse.tx-mouse.x)*.05; mouse.y += (mouse.ty-mouse.y)*.05;

  const p = ease(prog);
  // camera descend
  const y = THREE.MathUtils.lerp(H*.42, 2.2, p);
  const rad = THREE.MathUtils.lerp(26, 10, p) + Math.sin(p*Math.PI)*2.5;
  const ang = .78 + p*1.55 + mouse.x*.22;         // mouse orbits the camera slightly
  camera.position.set(Math.cos(ang)*rad, y + mouse.y*-2.2, Math.sin(ang)*rad);
  const lookY = THREE.MathUtils.lerp(TOWER_MID, Math.min(6, TOWER_MID), p) + mouse.y*.6;
  camera.lookAt(0, lookY, 0);
  sculpture.rotation.y += dt*.10;                  // slow idle turn
  sculpture.rotation.z = mouse.x*.03;              // subtle tilt toward cursor

  // chapter light rides down the tower
  chapLight.position.set(Math.cos(ang+.5)*4, THREE.MathUtils.lerp(H, 1, p), Math.sin(ang+.5)*4);

  renderer.render(scene, camera);
}
tick();

addEventListener('resize', ()=>{
  camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  scrollProg();
});
