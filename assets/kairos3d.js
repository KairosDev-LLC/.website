/* ==========================================================================
   kairos3d.js — the hero scene, rendered with WebGL
   A real 3D scene: perspective camera, depth-tested geometry, per-pixel
   lighting, textured device slabs carrying the actual App Store screens, and
   a planar reflection. No Three.js, no GSAP, no build step — raw WebGL2 with
   a WebGL1 fallback.

   Contract with the page:
   - Mounts into #gl-stage, which must contain <canvas id="gl-canvas"> and a
     no-WebGL fallback element (#stage-fallback).
   - Tabs are any [data-gl-tab] element; their index selects the front device.
   - If the context cannot be created, if the reader prefers reduced motion,
     or if this file never loads, the fallback stays visible and nothing here
     is required for the page to make sense.
   ========================================================================== */
(function () {
  'use strict';

  var stage = document.getElementById('gl-stage');
  var canvas = document.getElementById('gl-canvas');
  var fallback = document.getElementById('stage-fallback');
  if (!stage || !canvas) return;

  var reduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var gl = null;
  try {
    var opts = { alpha: true, antialias: true, premultipliedAlpha: false, powerPreference: 'high-performance' };
    gl = canvas.getContext('webgl2', opts) || canvas.getContext('webgl', opts);
  } catch (e) { gl = null; }
  if (!gl) return;                      // fallback markup stays on screen

  var isGL2 = typeof WebGL2RenderingContext !== 'undefined' &&
    gl instanceof WebGL2RenderingContext;

  // The scene is live, so hide the static fallback and show the canvas.
  canvas.hidden = false;
  if (fallback) fallback.hidden = true;
  stage.classList.add('gl-live');

  /* ---------------------------------------------------------------- maths */
  function mat4() {
    return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]);
  }
  function perspective(out, fovy, aspect, near, far) {
    var f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
    out[0]=f/aspect; out[1]=0; out[2]=0;  out[3]=0;
    out[4]=0; out[5]=f; out[6]=0; out[7]=0;
    out[8]=0; out[9]=0; out[10]=(far+near)*nf; out[11]=-1;
    out[12]=0; out[13]=0; out[14]=2*far*near*nf; out[15]=0;
    return out;
  }
  function lookAt(out, eye, center, up) {
    var z0=eye[0]-center[0], z1=eye[1]-center[1], z2=eye[2]-center[2];
    var len = Math.hypot(z0,z1,z2) || 1; z0/=len; z1/=len; z2/=len;
    var x0=up[1]*z2-up[2]*z1, x1=up[2]*z0-up[0]*z2, x2=up[0]*z1-up[1]*z0;
    len = Math.hypot(x0,x1,x2) || 1; x0/=len; x1/=len; x2/=len;
    var y0=z1*x2-z2*x1, y1=z2*x0-z0*x2, y2=z0*x1-z1*x0;
    out[0]=x0; out[1]=y0; out[2]=z0; out[3]=0;
    out[4]=x1; out[5]=y1; out[6]=z1; out[7]=0;
    out[8]=x2; out[9]=y2; out[10]=z2; out[11]=0;
    out[12]=-(x0*eye[0]+x1*eye[1]+x2*eye[2]);
    out[13]=-(y0*eye[0]+y1*eye[1]+y2*eye[2]);
    out[14]=-(z0*eye[0]+z1*eye[1]+z2*eye[2]);
    out[15]=1;
    return out;
  }
  function multiply(out, a, b) {
    for (var c = 0; c < 4; c++) {
      var b0=b[c*4], b1=b[c*4+1], b2=b[c*4+2], b3=b[c*4+3];
      out[c*4]   = b0*a[0] + b1*a[4] + b2*a[8]  + b3*a[12];
      out[c*4+1] = b0*a[1] + b1*a[5] + b2*a[9]  + b3*a[13];
      out[c*4+2] = b0*a[2] + b1*a[6] + b2*a[10] + b3*a[14];
      out[c*4+3] = b0*a[3] + b1*a[7] + b2*a[11] + b3*a[15];
    }
    return out;
  }
  function compose(out, tx, ty, tz, ry, rx, sx, sy, sz) {
    // M = T * Ry * Rx * S, written out column-major the way WebGL wants it.
    var cy = Math.cos(ry), sy2 = Math.sin(ry);
    var cx = Math.cos(rx), sx2 = Math.sin(rx);
    // Ry * Rx, as a 3x3 in column-major order
    var m00 = cy,  m01 = sy2 * sx2,  m02 = sy2 * cx;
    var m10 = 0,   m11 = cx,         m12 = -sx2;
    var m20 = -sy2, m21 = cy * sx2,  m22 = cy * cx;
    out[0] = m00 * sx; out[1] = m10 * sx; out[2] = m20 * sx; out[3] = 0;
    out[4] = m01 * sy; out[5] = m11 * sy; out[6] = m21 * sy; out[7] = 0;
    out[8] = m02 * sz; out[9] = m12 * sz; out[10] = m22 * sz; out[11] = 0;
    out[12] = tx; out[13] = ty; out[14] = tz; out[15] = 1;
    return out;
  }

  function inverseTranspose3(m) {
    // Rotation-only models here, so the upper 3x3 is orthogonal up to scale.
    return new Float32Array([m[0],m[1],m[2], m[4],m[5],m[6], m[8],m[9],m[10]]);
  }

  /* -------------------------------------------------------------- shaders */
  var VS = [
    'precision highp float;',
    'attribute vec3 aPos;',
    'attribute vec3 aNormal;',
    'attribute vec2 aUV;',
    'uniform mat4 uProj, uView, uModel;',
    'uniform mat3 uNormalMat;',
    'uniform float uFlipY, uFloorY;',
    'varying vec3 vNormal, vWorld;',
    'varying vec2 vUV;',
    'void main() {',
    '  vec4 world = uModel * vec4(aPos, 1.0);',
    '  if (uFlipY < 0.0) { world.y = 2.0 * uFloorY - world.y; }',
    '  vWorld = world.xyz;',
    '  vNormal = normalize(uNormalMat * aNormal) * vec3(1.0, uFlipY, 1.0);',
    '  vUV = aUV;',
    '  gl_Position = uProj * uView * world;',
    '}'
  ].join('\n');

  var FS = [
    'precision highp float;',
    'varying vec3 vNormal, vWorld;',
    'varying vec2 vUV;',
    'uniform sampler2D uTex;',
    'uniform vec3 uEye, uTint;',
    'uniform float uIsScreen, uAlpha, uRadius, uAspect, uGlow;',
    // Rounded-rectangle mask in UV space so the slab reads as a device.
    'float roundedMask(vec2 uv, float r) {',
    '  vec2 p = (uv - 0.5) * vec2(uAspect, 1.0);',
    '  vec2 half_ = vec2(0.5 * uAspect, 0.5) - vec2(r);',
    '  vec2 d = abs(p) - half_;',
    '  float dist = length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r;',
    '  return 1.0 - smoothstep(-0.004, 0.004, dist);',
    '}',
    'void main() {',
    '  vec3 N = normalize(vNormal);',
    '  vec3 V = normalize(uEye - vWorld);',
    '  vec3 L = normalize(vec3(-0.45, 0.85, 0.75));',
    '  vec3 L2 = normalize(vec3(0.9, 0.15, -0.5));',
    '  float diff = max(dot(N, L), 0.0);',
    '  float rim = pow(1.0 - max(dot(N, V), 0.0), 2.6);',
    '  vec3 H = normalize(L + V);',
    '  float spec = pow(max(dot(N, H), 0.0), 64.0);',
    '  vec3 base;',
    '  float a = uAlpha;',
    '  if (uIsScreen > 0.5) {',
    '    float m = roundedMask(vUV, uRadius);',
    '    if (m < 0.01) discard;',
    '    vec3 tex = texture2D(uTex, vec2(vUV.x, 1.0 - vUV.y)).rgb;',
    '    base = tex * (0.72 + 0.42 * diff);',
    '    base += vec3(1.0, 0.42, 0.16) * rim * 0.42 * uGlow;',
    '    base += vec3(1.0) * spec * 0.28;',
    '    a *= m;',
    '  } else {',
    '    base = uTint * (0.30 + 0.75 * diff);',
    '    base += vec3(1.0, 0.35, 0.12) * rim * 0.55 * uGlow;',
    '    base += vec3(1.0) * spec * 0.22;',
    '  }',
    '  base += max(dot(N, L2), 0.0) * vec3(0.16, 0.20, 0.42) * 0.5;',
    '  gl_FragColor = vec4(base, a);',
    '}'
  ].join('\n');

  function shader(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(s) || 'shader compile failed');
    }
    return s;
  }

  var prog;
  try {
    prog = gl.createProgram();
    gl.attachShader(prog, shader(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, shader(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(prog) || 'link failed');
    }
  } catch (err) {
    // A broken pipeline must not take the page with it.
    canvas.hidden = true;
    if (fallback) fallback.hidden = false;
    stage.classList.remove('gl-live');
    return;
  }
  gl.useProgram(prog);

  var loc = {};
  ['uProj','uView','uModel','uNormalMat','uEye','uTex','uIsScreen','uAlpha','uTint','uRadius','uAspect','uFlipY','uFloorY','uGlow']
    .forEach(function (n) { loc[n] = gl.getUniformLocation(prog, n); });
  var aPos = gl.getAttribLocation(prog, 'aPos');
  var aNormal = gl.getAttribLocation(prog, 'aNormal');
  var aUV = gl.getAttribLocation(prog, 'aUV');

  /* ------------------------------------------------------------- geometry */
  // A slab: front face (textured), back and four sides (tinted body).
  function slab(w, h, d) {
    var x = w / 2, y = h / 2, z = d / 2;
    var P = [], N = [], U = [], I = [];
    function face(verts, nrm, uvs) {
      var base = P.length / 3;
      for (var i = 0; i < 4; i++) {
        P.push(verts[i][0], verts[i][1], verts[i][2]);
        N.push(nrm[0], nrm[1], nrm[2]);
        U.push(uvs[i][0], uvs[i][1]);
      }
      I.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    // front (+z) — index 0..3 is the screen
    face([[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]], [0,0,1], [[0,0],[1,0],[1,1],[0,1]]);
    face([[x,-y,-z],[-x,-y,-z],[-x,y,-z],[x,y,-z]], [0,0,-1], [[0,0],[1,0],[1,1],[0,1]]);
    face([[x,-y,z],[x,-y,-z],[x,y,-z],[x,y,z]], [1,0,0], [[0,0],[1,0],[1,1],[0,1]]);
    face([[-x,-y,-z],[-x,-y,z],[-x,y,z],[-x,y,-z]], [-1,0,0], [[0,0],[1,0],[1,1],[0,1]]);
    face([[-x,y,z],[x,y,z],[x,y,-z],[-x,y,-z]], [0,1,0], [[0,0],[1,0],[1,1],[0,1]]);
    face([[-x,-y,-z],[x,-y,-z],[x,-y,z],[-x,-y,z]], [0,-1,0], [[0,0],[1,0],[1,1],[0,1]]);
    return { pos: new Float32Array(P), nrm: new Float32Array(N), uv: new Float32Array(U),
             idx: new Uint16Array(I) };
  }

  function upload(mesh) {
    var b = {};
    b.pos = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b.pos);
    gl.bufferData(gl.ARRAY_BUFFER, mesh.pos, gl.STATIC_DRAW);
    b.nrm = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b.nrm);
    gl.bufferData(gl.ARRAY_BUFFER, mesh.nrm, gl.STATIC_DRAW);
    b.uv = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b.uv);
    gl.bufferData(gl.ARRAY_BUFFER, mesh.uv, gl.STATIC_DRAW);
    b.idx = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.idx);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, mesh.idx, gl.STATIC_DRAW);
    b.count = mesh.idx.length;
    return b;
  }

  var FLOOR_Y = -1.42;
  var sceneScale = 1;   // shrinks the whole scene to fit narrow viewports
  var PHONE_ASPECT = 720 / 1558;
  var phone = upload(slab(1.18, 1.18 / PHONE_ASPECT, 0.085));

  function bind(b) {
    gl.bindBuffer(gl.ARRAY_BUFFER, b.pos);
    gl.enableVertexAttribArray(aPos); gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, b.nrm);
    gl.enableVertexAttribArray(aNormal); gl.vertexAttribPointer(aNormal, 3, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ARRAY_BUFFER, b.uv);
    gl.enableVertexAttribArray(aUV); gl.vertexAttribPointer(aUV, 2, gl.FLOAT, false, 0, 0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, b.idx);
  }

  /* -------------------------------------------------------------- texture */
  function makeTexture(src) {
    var tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    // 1x1 placeholder so the first frames render before the image lands.
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE,
      new Uint8Array([24, 24, 28, 255]));
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

    var img = new Image();
    img.decoding = 'async';
    img.onload = function () {
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
      if (isGL2) {
        gl.generateMipmap(gl.TEXTURE_2D);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      }
      var ext = gl.getExtension('EXT_texture_filter_anisotropic');
      if (ext) {
        gl.texParameterf(gl.TEXTURE_2D, ext.TEXTURE_MAX_ANISOTROPY_EXT,
          Math.min(8, gl.getParameter(ext.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
      }
      dirty = true;
    };
    img.src = src;
    return tex;
  }

  var SCREENS = [
    { src: '/assets/shots/app-1-working.webp', label: 'On duty', pattern: 'D..' },
    { src: '/assets/shots/app-2-calendar.webp', label: 'Calendar', pattern: 'DD..DDD..DD...' },
    { src: '/assets/shots/app-3-vacation.webp', label: 'Vacation', pattern: 'D.D.D....' }
  ];
  SCREENS.forEach(function (s) { s.tex = makeTexture(s.src); });

  /* ----------------------------------------------------------- scene state */
  var proj = mat4(), view = mat4(), model = mat4();
  var eye = [0, 0.15, 6.2];
  var front = 0;                     // which screen is centre stage
  var orbit = { x: -0.04, y: 0.34 }; // current camera orbit
  var target = { x: -0.04, y: 0.34 };
  var drag = null;
  var dirty = true;
  var t0 = performance.now();

  function layoutFor(i) {
    // Positions on an arc: front centre, others swung back and out.
    var rel = i - front;
    var n = SCREENS.length;
    if (rel > n / 2) rel -= n;
    if (rel < -n / 2) rel += n;
    return {
      x: rel * 1.42,
      y: Math.abs(rel) * -0.06,
      z: -Math.abs(rel) * 0.95,
      ry: -rel * 0.5,
      s: rel === 0 ? 1 : 0.9
    };
  }
  var placed = SCREENS.map(function (_, i) {
    var l = layoutFor(i);
    return { x: l.x, y: l.y, z: l.z, ry: l.ry, s: l.s };
  });

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var w = Math.max(1, Math.round(stage.clientWidth * dpr));
    var h = Math.max(1, Math.round(stage.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
      dirty = true;
    }
    return w / h;
  }


  // A ring of day tiles orbiting the devices: the selected rotation repeated
  // around a full turn, on-duty tiles lit, off-duty tiles dark. It is the
  // rotation itself, rendered as a rotation.
  var RING_PATTERN = SCREENS[0].pattern;
  var ringTiles = [];
  var ring = upload(slab(0.34, 0.23, 0.05));
  var RING_R = 2.78;

  function buildRing() {
    var out = '';
    while (out.length < 28) { out += RING_PATTERN; }
    ringTiles = out.split('');
  }
  buildRing();

  function drawRing(flipY) {
    var n = ringTiles.length;
    var spin = reduced ? 0 : (performance.now() - t0) * 0.00007;
    gl.uniform1f(loc.uIsScreen, 0.0);
    bind(ring);
    for (var i = 0; i < n; i++) {
      var a = (i / n) * Math.PI * 2 + spin;
      var on = ringTiles[i];
      var wave = Math.sin(a * 3 + spin * 6) * 0.05;
      compose(model, Math.sin(a) * RING_R * sceneScale, (-0.90 + wave) * sceneScale,
              Math.cos(a) * RING_R * sceneScale, a, 0.30,
              sceneScale, sceneScale, sceneScale);
      gl.uniformMatrix4fv(loc.uModel, false, model);
      gl.uniformMatrix3fv(loc.uNormalMat, false, inverseTranspose3(model));
      gl.uniform1f(loc.uAlpha, flipY < 0 ? 0.10 : 0.95);
      if (on === 'D') { gl.uniform3f(loc.uTint, 1.0, 0.42, 0.16); gl.uniform1f(loc.uGlow, 1.4); }
      else if (on === 'N') { gl.uniform3f(loc.uTint, 0.45, 0.58, 1.0); gl.uniform1f(loc.uGlow, 1.1); }
      else { gl.uniform3f(loc.uTint, 0.15, 0.15, 0.18); gl.uniform1f(loc.uGlow, 0.25); }
      gl.drawElements(gl.TRIANGLES, ring.count, gl.UNSIGNED_SHORT, 0);
    }
  }

  function drawScene(flipY) {
    gl.uniform1f(loc.uFlipY, flipY);
    gl.uniform1f(loc.uFloorY, FLOOR_Y * sceneScale);
    drawRing(flipY);
    bind(phone);
    for (var i = 0; i < SCREENS.length; i++) {
      var p = placed[i];
      var bob = reduced ? 0 : Math.sin((performance.now() - t0) * 0.0006 + i * 1.7) * 0.045;
      compose(model, p.x * sceneScale, (p.y + bob) * sceneScale, p.z * sceneScale,
              p.ry, 0.02, p.s * sceneScale, p.s * sceneScale, p.s * sceneScale);
      gl.uniformMatrix4fv(loc.uModel, false, model);
      gl.uniformMatrix3fv(loc.uNormalMat, false, inverseTranspose3(model));
      gl.uniform1f(loc.uAlpha, flipY < 0 ? 0.16 : 1.0);
      gl.uniform1f(loc.uGlow, i === front ? 1.0 : 0.55);

      // body first, then the textured screen face
      gl.uniform1f(loc.uIsScreen, 0.0);
      gl.uniform3f(loc.uTint, 0.075, 0.075, 0.085);
      gl.drawElements(gl.TRIANGLES, phone.count - 6, gl.UNSIGNED_SHORT, 6 * 2);

      gl.uniform1f(loc.uIsScreen, 1.0);
      gl.uniform1f(loc.uAspect, PHONE_ASPECT);
      gl.uniform1f(loc.uRadius, 0.055);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, SCREENS[i].tex);
      gl.uniform1i(loc.uTex, 0);
      gl.drawElements(gl.TRIANGLES, 6, gl.UNSIGNED_SHORT, 0);
    }
  }

  function render() {
    var aspect = resize();
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.enable(gl.CULL_FACE);

    // Narrow viewports get the whole scene scaled down rather than cropped.
    // The scene's bounding box is ~6.4 x 3.6 units; fit it to whatever the
    // viewport gives us instead of cropping the ring off the edges.
    sceneScale = Math.min(1, Math.max(0.55, 0.62 * aspect));
    perspective(proj, 42 * Math.PI / 180, aspect, 0.1, 60);
    var r = 5.15 + dolly * 2.4;
    eye[0] = Math.sin(orbit.y) * Math.cos(orbit.x) * r;
    eye[1] = Math.sin(orbit.x) * r + 0.25;
    eye[2] = Math.cos(orbit.y) * Math.cos(orbit.x) * r;
    lookAt(view, eye, [0, -dolly * 0.55, 0], [0, 1, 0]);
    gl.uniformMatrix4fv(loc.uProj, false, proj);
    gl.uniformMatrix4fv(loc.uView, false, view);
    gl.uniform3f(loc.uEye, eye[0], eye[1], eye[2]);

    // Planar reflection under the devices, then the devices themselves.
    gl.depthMask(false);
    gl.cullFace(gl.FRONT);
    drawScene(-1.0);
    gl.depthMask(true);
    gl.cullFace(gl.BACK);
    drawScene(1.0);
  }

  /* -------------------------------------------------------- animation loop */
  var running = true;
  var settledFrames = 0;

  function frame() {
    if (!running) return;
    // Reduced motion means no idle animation at all: snap to the target,
    // draw the result, and stop asking for frames until something changes.
    var easing = reduced ? 1 : 0.10;
    var moved = Math.abs(target.x - orbit.x) + Math.abs(target.y - orbit.y);
    orbit.x += (target.x - orbit.x) * easing;
    orbit.y += (target.y - orbit.y) * easing;
    placed.forEach(function (p, i) {
      var l = layoutFor(i);
      moved += Math.abs(l.x - p.x) + Math.abs(l.z - p.z) + Math.abs(l.ry - p.ry);
      p.x += (l.x - p.x) * easing;
      p.y += (l.y - p.y) * easing;
      p.z += (l.z - p.z) * easing;
      p.ry += (l.ry - p.ry) * easing;
      p.s += (l.s - p.s) * easing;
    });
    render();

    if (reduced) {
      settledFrames = moved < 0.001 ? settledFrames + 1 : 0;
      if (settledFrames > 2) { running = false; return; }
    }
    window.requestAnimationFrame(frame);
  }

  function wake() {
    settledFrames = 0;
    if (!running) { running = true; window.requestAnimationFrame(frame); }
  }

  /* ------------------------------------------------------------ interaction */
  var idleSpin = !reduced;
  function pointerAngle(e) {
    var r = stage.getBoundingClientRect();
    var nx = (e.clientX - r.left) / r.width - 0.5;
    var ny = (e.clientY - r.top) / r.height - 0.5;
    target.y = 0.55 + nx * 1.15;
    target.x = -0.06 - ny * 0.45;
  }

  if (!reduced) {
    stage.addEventListener('pointermove', function (e) {
      if (drag) {
        target.y = drag.y + (drag.px - e.clientX) * 0.006;
        target.x = Math.max(-0.6, Math.min(0.6, drag.x + (drag.py - e.clientY) * 0.004));
      } else if (e.pointerType !== 'touch') {
        idleSpin = false;
        pointerAngle(e);
      }
    }, { passive: true });
    stage.addEventListener('pointerdown', function (e) {
      drag = { px: e.clientX, py: e.clientY, x: target.x, y: target.y };
      stage.setPointerCapture && stage.setPointerCapture(e.pointerId);
      stage.classList.add('is-grabbing');
    });
    window.addEventListener('pointerup', function () {
      drag = null; stage.classList.remove('is-grabbing');
    });
    stage.addEventListener('pointerleave', function () {
      idleSpin = true;
    });
    // Idle drift so the scene is alive before anyone touches it.
    window.setInterval(function () {
      if (idleSpin && !drag && !document.hidden) {
        target.y = 0.34 + Math.sin(performance.now() * 0.00021) * 0.30;
        target.x = -0.04 + Math.cos(performance.now() * 0.00017) * 0.08;
      }
    }, 60);
  }

  // Scroll dolly: the scene tilts and pulls back as the hero scrolls away, so
  // the transition into the gallery below reads as camera movement.
  var dolly = 0;
  if (!reduced) {
    window.addEventListener('scroll', function () {
      var r = stage.getBoundingClientRect();
      var p = Math.max(0, Math.min(1, -r.top / Math.max(1, r.height)));
      if (Math.abs(p - dolly) > 0.002) { dolly = p; wake(); }
    }, { passive: true });
  }

  // Tabs pick the front device.
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[data-gl-tab]'));
  function select(i) {
    front = (i + SCREENS.length) % SCREENS.length;
    RING_PATTERN = SCREENS[front].pattern;
    buildRing();
    tabs.forEach(function (tab, k) {
      var on = k === front;
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      tab.tabIndex = on ? 0 : -1;
    });
    wake();
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { select(i); });
    tab.addEventListener('keydown', function (e) {
      var d = e.key === 'ArrowRight' ? 1 : (e.key === 'ArrowLeft' ? -1 : 0);
      if (!d) return;
      e.preventDefault();
      select(front + d);
      tabs[front].focus();
    });
  });
  if (tabs.length) select(0);

  // Only render while the stage is on screen.
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { wake(); }
        else { running = false; }
      });
    }, { threshold: 0.02 }).observe(stage);
  }
  window.addEventListener('resize', function () { dirty = true; wake(); }, { passive: true });

  frame();
}());
