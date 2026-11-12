// Solo las piezas de three.js que usa panel/espacio.js. tools/panel.py arma con esto
// dist/vendor/three.matriz.min.js (esbuild), así la copia minificada no vive en el repositorio.
export {
  WebGLRenderer, Scene, PerspectiveCamera, Group, Mesh, MeshBasicMaterial, SphereGeometry,
  BufferGeometry, Float32BufferAttribute, LineBasicMaterial, LineSegments, Points, PointsMaterial,
  Color, Vector3, Raycaster, Vector2, AdditiveBlending, CanvasTexture, SpriteMaterial, Sprite,
  RingGeometry, DoubleSide, MathUtils, Clock, Fog,
} from "three";
