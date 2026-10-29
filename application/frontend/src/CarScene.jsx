
import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { ContactShadows, Environment, useGLTF } from '@react-three/drei'
import * as THREE from 'three'

function PorscheModel() {
  const groupRef = useRef(null)
  const { scene } = useGLTF('/models/porsche.glb')

  const { model, scale, position } = useMemo(() => {
    const model = scene.clone(true)
    const bounds = new THREE.Box3().setFromObject(model)
    const size = bounds.getSize(new THREE.Vector3())
    const center = bounds.getCenter(new THREE.Vector3())

    const maxDimension = Math.max(size.x, size.y, size.z) || 1
    const scale = 3.8 / maxDimension

    model.traverse((object) => {
      if (!object.isMesh) return

      object.castShadow = true
      object.receiveShadow = true

      if (object.material) {
        object.material = Array.isArray(object.material)
          ? object.material.map((material) => material.clone())
          : object.material.clone()
      }
    })

    return {
      model,
      scale,
      position: [
        -center.x * scale,
        -bounds.min.y * scale,
        -center.z * scale,
      ],
    }
  }, [scene])

  useEffect(() => {
    if (!groupRef.current) return

    groupRef.current.scale.setScalar(scale)
    groupRef.current.rotation.y = -0.45
  }, [])

  useFrame((state, delta) => {
    const group = groupRef.current
    if (!group) return

    const progress = THREE.MathUtils.clamp(
      window.scrollY / (window.innerHeight * 0.8),
      0,
      1,
    )

    const eased = progress * progress * (3 - 2 * progress)

    // Fade/scale in smoothly on first load.
    group.scale.setScalar(scale)

    // Scroll-controlled rotation around the real 3D model.
    const targetYaw = THREE.MathUtils.lerp(-0.45, 0.35, eased)
    group.rotation.y = THREE.MathUtils.damp(
      group.rotation.y,
      targetYaw,
      3,
      delta,
    )

    group.rotation.x = THREE.MathUtils.damp(
      group.rotation.x,
      -eased * 0.025,
      3,
      delta,
    )

    group.position.y = THREE.MathUtils.damp(
      group.position.y,
      position[1] + Math.sin(state.clock.elapsedTime * 0.8) * 0.025,
      3,
      delta,
    )
  })

  return (
    <group ref={groupRef} position={position}>
      <primitive object={model} />
    </group>
  )
}

function SceneContents() {
  return (
    <>
      <ambientLight intensity={1.8} />
      <hemisphereLight
        args={['#fff4e5', '#8b715a', 2]}
      />
      <directionalLight
        position={[4, 7, 5]}
        intensity={3.2}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <spotLight
        position={[-5, 5, -3]}
        intensity={2}
        angle={0.65}
        penumbra={1}
      />

      <Suspense fallback={null}>
        <PorscheModel />
        <ContactShadows
          position={[0, 0.015, 0]}
          opacity={0.42}
          scale={8}
          blur={3}
          far={4}
          color="#493426"
        />
        <Environment preset="studio" />
      </Suspense>
    </>
  )
}

export default function CarScene() {
  return (
    <div className="car-scene" aria-label="Interactive 3D sports car">
      <Canvas
        shadows
        dpr={[1, 1.5]}
        camera={{ position: [0, 2.8, 5.0], fov: 35 }}
        gl={{ alpha: true, antialias: true }}
        onCreated={({ gl }) => {
          gl.setClearColor('#000000', 0)
          gl.toneMapping = THREE.ACESFilmicToneMapping
          gl.toneMappingExposure = 1.15
        }}
      >
        <SceneContents />
      </Canvas>
    </div>
  )
}

useGLTF.preload('/models/porsche.glb')
