import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { useReducedMotion } from 'framer-motion'

function terrainHeight(x: number, z: number) {
  const ridge = Math.sin(x * 1.45 + z * 0.42) * 0.16
  const basin = Math.cos(z * 1.8 - x * 0.32) * 0.11
  const peakA = Math.exp(-((x - 0.7) ** 2 + (z + 0.35) ** 2) * 0.9) * 0.48
  const peakB = Math.exp(-((x + 0.95) ** 2 + (z - 0.65) ** 2) * 1.3) * 0.3
  return ridge + basin + peakA + peakB
}

function Terrain() {
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(4.7, 4.7, 100, 100)
    geo.rotateX(-Math.PI / 2)
    const positions = geo.attributes.position
    const colors = new Float32Array(positions.count * 3)
    const low = new THREE.Color('#123746')
    const high = new THREE.Color('#36B4CF')
    const accent = new THREE.Color('#D83995')
    for (let i = 0; i < positions.count; i += 1) {
      const x = positions.getX(i)
      const z = positions.getZ(i)
      const y = terrainHeight(x, z)
      positions.setY(i, y)
      const t = THREE.MathUtils.clamp((y + 0.12) / 0.62, 0, 1)
      const color = low.clone().lerp(high, t * 0.72)
      if (t > 0.68) color.lerp(accent, (t - 0.68) * 0.7)
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geo.computeVertexNormals()
    return geo
  }, [])

  const contours = useMemo(() => {
    return [0.42, 0.72, 1.02, 1.32, 1.62, 1.92].map((radius, index) => {
      const points: THREE.Vector3[] = []
      for (let i = 0; i <= 180; i += 1) {
        const angle = (i / 180) * Math.PI * 2
        const wobble = Math.sin(angle * 3 + index) * 0.055 + Math.cos(angle * 5) * 0.025
        const x = Math.cos(angle) * (radius + wobble)
        const z = Math.sin(angle) * (radius + wobble)
        points.push(new THREE.Vector3(x, terrainHeight(x, z) + 0.018, z))
      }
      const curve = new THREE.CatmullRomCurve3(points)
      return new THREE.BufferGeometry().setFromPoints(curve.getPoints(220))
    })
  }, [])

  return (
    <group>
      <mesh geometry={geometry} position={[0, -0.08, 0]} receiveShadow>
        <meshPhysicalMaterial vertexColors roughness={0.82} metalness={0.08} clearcoat={0.24} />
      </mesh>
      <mesh geometry={geometry} position={[0, -0.065, 0]}>
        <meshBasicMaterial color="#B7F2F5" wireframe transparent opacity={0.055} />
      </mesh>
      {contours.map((line, index) => (
        <primitive key={index} object={new THREE.Line(line, new THREE.LineBasicMaterial({
          color: index === 4 ? '#E875B6' : '#8BE0E8',
          transparent: true,
          opacity: index === 4 ? 0.56 : 0.3,
        }))} />
      ))}
      <mesh position={[0, -0.38, 0]}>
        <boxGeometry args={[4.86, 0.18, 4.86]} />
        <meshStandardMaterial color="#0A202D" roughness={0.46} metalness={0.32} />
      </mesh>
      {([[0.72, 0.48], [-1.02, 0.65], [0.18, -1.12]] as [number, number][]).map(([x, z], index) => (
        <group key={index} position={[x, terrainHeight(x, z) + 0.04, z]}>
          <mesh>
            <cylinderGeometry args={[0.012, 0.012, 0.34, 8]} />
            <meshStandardMaterial color={index === 1 ? '#D83995' : '#8BE0E8'} emissive={index === 1 ? '#D83995' : '#0593C6'} emissiveIntensity={0.25} />
          </mesh>
          <mesh position={[0, 0.19, 0]}>
            <sphereGeometry args={[0.055, 16, 16]} />
            <meshStandardMaterial color={index === 1 ? '#D83995' : '#B8F2F6'} emissive={index === 1 ? '#D83995' : '#0593C6'} emissiveIntensity={0.65} />
          </mesh>
        </group>
      ))}
    </group>
  )
}

function Scene() {
  const group = useRef<THREE.Group>(null)
  const reducedMotion = useReducedMotion()
  useFrame((state, delta) => {
    if (!group.current || reducedMotion) return
    group.current.rotation.y += delta * 0.035
    group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, -0.12 + state.pointer.y * 0.035, 0.025)
  })
  return (
    <group ref={group} rotation={[-0.13, -0.28, 0]} position={[0, -0.1, 0]}>
      <Terrain />
    </group>
  )
}

export default function KnowledgeAtlas() {
  return (
    <div className="knowledge-atlas-canvas" role="img" aria-label="A three-dimensional topographic knowledge map, with document locations marked across layered terrain">
      <Canvas camera={{ position: [5.3, 4.8, 6.4], fov: 34 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: true }} onCreated={({ gl }) => { gl.setClearColor('#071A25', 0) }}>
        <ambientLight intensity={1.35} />
        <directionalLight position={[4, 7, 5]} intensity={2.4} color="#E7FBFF" />
        <pointLight position={[-3, 2, -2]} intensity={18} distance={8} color="#D83995" />
        <pointLight position={[3, 1, 3]} intensity={14} distance={7} color="#0593C6" />
        <Scene />
      </Canvas>
    </div>
  )
}
