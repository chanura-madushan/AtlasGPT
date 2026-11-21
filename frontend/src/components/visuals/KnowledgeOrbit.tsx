import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Float, Line } from '@react-three/drei'
import { useReducedMotion } from 'framer-motion'
import type { Group } from 'three'

function OrbitScene() {
  const group = useRef<Group>(null)
  const reducedMotion = useReducedMotion()

  useFrame((_, delta) => {
    if (group.current && !reducedMotion) {
      group.current.rotation.y += delta * 0.12
      group.current.rotation.x = Math.sin(Date.now() * 0.00018) * 0.08
    }
  })

  const nodes: [number, number, number][] = [
    [0, 0, 0],
    [1.35, 0.45, 0.15],
    [-1.2, 0.65, -0.2],
    [0.35, -1.25, 0.25],
    [-0.65, -0.95, -0.3],
    [0.35, 1.25, -0.2],
    [1.05, -0.7, -0.25],
  ]

  const edges: [number, number, number][][] = [
    [nodes[0], nodes[1]], [nodes[0], nodes[2]], [nodes[0], nodes[3]],
    [nodes[0], nodes[4]], [nodes[0], nodes[5]], [nodes[1], nodes[6]],
    [nodes[3], nodes[6]], [nodes[2], nodes[5]], [nodes[4], nodes[3]],
  ]

  return (
    <group ref={group}>
      <mesh>
        <icosahedronGeometry args={[0.62, 2]} />
        <meshStandardMaterial color="#102B3A" roughness={0.28} metalness={0.32} />
      </mesh>
      <mesh>
        <icosahedronGeometry args={[0.66, 1]} />
        <meshBasicMaterial color="#39B6DE" wireframe transparent opacity={0.24} />
      </mesh>
      {edges.map((edge, index) => (
        <Line key={index} points={edge} color={index % 3 === 0 ? '#D83995' : '#0593C6'} lineWidth={1.2} transparent opacity={0.55} />
      ))}
      {nodes.slice(1).map((position, index) => (
        <Float key={index} speed={reducedMotion ? 0 : 1.1 + index * 0.12} floatIntensity={reducedMotion ? 0 : 0.12}>
          <mesh position={position}>
            <sphereGeometry args={[index % 2 === 0 ? 0.095 : 0.075, 20, 20]} />
            <meshStandardMaterial color={index % 3 === 0 ? '#D83995' : '#28A9D1'} emissive={index % 3 === 0 ? '#D83995' : '#0593C6'} emissiveIntensity={0.35} roughness={0.25} />
          </mesh>
        </Float>
      ))}
      <mesh rotation={[Math.PI / 2.7, 0.2, 0]}>
        <torusGeometry args={[1.85, 0.006, 8, 120]} />
        <meshBasicMaterial color="#0593C6" transparent opacity={0.28} />
      </mesh>
      <mesh rotation={[0.8, 0.4, 0.9]}>
        <torusGeometry args={[2.05, 0.005, 8, 120]} />
        <meshBasicMaterial color="#D83995" transparent opacity={0.22} />
      </mesh>
    </group>
  )
}

export default function KnowledgeOrbit() {
  return (
    <div className="knowledge-orbit" role="img" aria-label="A three-dimensional network of connected knowledge nodes">
      <Canvas camera={{ position: [0, 0, 5.8], fov: 42 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: true }} fallback={<div className="knowledge-orbit__fallback" />}>
        <ambientLight intensity={1.2} />
        <pointLight position={[4, 4, 4]} intensity={2} color="#FFFFFF" />
        <pointLight position={[-3, -2, 2]} intensity={1.1} color="#D83995" />
        <OrbitScene />
      </Canvas>
    </div>
  )
}
