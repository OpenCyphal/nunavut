#ifndef HELPERS_H
#define HELPERS_H

#ifndef NUNAVUT_ASSERT
  #include <assert.h>
  #define NUNAVUT_ASSERT assert
#endif

#ifndef __ADSPTS__
  #define NAN32 NAN
  #define NAN64 NAN
  #define INF32 INFINITY
  #define INF64 INFINITY
#else

  #include <stdint.h>

  #define uint64_FloatExpMask       0x7FFF000000000000ULL
  #define uint64_FloatSignalingFlag 0x0000800000000000ULL
  #define uint64_FloatMantisaMask   0x0000FFFFFFFFFFFFULL
  #define uint64_FloatSignMask      0x8000000000000000ULL
  #define uint64_FloatPlusInf       uint64_FloatExpMask  
  #define uint64_FloatMinusInf     (uint64_FloatExpMask | uint64_FloatSignMask)
  #define uint64_sNaN               0x7FFFFFFFFFFFFFFFULL
  #define uint64_qNaN              (uint64_sNaN & (~uint64_FloatSignalingFlag))

  typedef union { uint64_t integer; double real; } TUintFloat64;
  inline bool is_nan64( double x )
  {
    TUintFloat64 u; u.real = x;
    return (u.integer & uint64_FloatExpMask) == uint64_FloatExpMask && (u.integer & uint64_FloatMantisaMask) != 0;
  }
  inline bool is_signaling_nan64( double x )
  {
    TUintFloat64 u; u.real = x;
    return (u.integer & uint64_FloatExpMask) == uint64_FloatExpMask && (u.integer & uint64_FloatSignalingFlag);
  }
  inline double qnan64(void)
  {
    TUintFloat64 u; u.integer = uint64_qNaN;
    return u.real;
  }
  inline double snan64(void)
  {
    TUintFloat64 u; u.integer = uint64_sNaN;
    return u.real;
  }
  inline bool is_inf64( double x )
  {
    TUintFloat64 u; u.real = x;
    return (u.integer & uint64_FloatExpMask) == uint64_FloatExpMask && (u.integer & uint64_FloatMantisaMask) == 0;
  }
  inline float inf64(void)
  {
    TUintFloat64 u; u.integer = uint64_FloatPlusInf;
    return u.real;
  }
  inline bool is_finite64( double x )
  {
    TUintFloat64 u; u.real = x;
    return (u.integer & uint64_FloatExpMask) != uint64_FloatExpMask;
  }

  #define uint32_FloatExpMask       0x7F800000UL
  #define uint32_FloatSignalingFlag 0x00400000UL
  #define uint32_FloatMantisaMask   0x003FFFFFUL
  #define uint32_FloatSignMask      0x80000000UL
  #define uint32_FloatPlusInf       uint32_FloatExpMask
  #define uint32_FloatMinusInf     (uint32_FloatExpMask | uint32_FloatsignMask)
  #define uint32_sNaN               0x7FFFFFFFUL
  #define uint32_qNaN              (uint32_sNaN & (~uint32_FloatSignalingFlag))

  typedef union { uint32_t integer; float real; } TUintFloat32;
  inline bool is_nan32( float x )
  {
    TUintFloat32 u; u.real = x;
    return (u.integer & uint32_FloatExpMask) == uint32_FloatExpMask && (u.integer & uint32_FloatMantisaMask) != 0;
  }
  inline bool is_signaling_nan32( float x )
  {
    TUintFloat32 u; u.real = x;
    return (u.integer & uint32_FloatExpMask) == uint32_FloatExpMask && (u.integer & uint32_FloatSignalingFlag);
  }
  inline float qnan32(void)
  {
    TUintFloat32 u; u.integer = uint32_qNaN;
    return u.real;
  }
  inline float snan32(void)
  {
    TUintFloat32 u; u.integer = uint32_sNaN;
    return u.real;
  }
  inline bool is_inf32( float x )
  {
    TUintFloat32 u; u.real = x;
    return (u.integer & uint32_FloatExpMask) == uint32_FloatExpMask && (u.integer & uint32_FloatMantisaMask) == 0;
  }
  inline float inf32(void)
  {
    TUintFloat32 u; u.integer = uint32_FloatPlusInf;
    return u.real;
  }
  inline bool is_finite32( float x )
  {
    TUintFloat32 u; u.real = x;
    return (u.integer & uint32_FloatExpMask) != uint32_FloatExpMask;
  }
  #define NAN32 qnan32()
  #define NAN64 qnan64()
  #define INF32 inf32 ()
  #define INF64 inf64 ()
  #define isfinite(x) ( sizeof(x) == sizeof(float) ? is_finite32(x) : is_finite64(x) )
  #define static_assert(cond,msg)

  //#define static_assert(cond,msg) typedef int static_assert_foo_t[(cond) ? 1 : -1]
  /*
  #define ASSERT_CONCAT_(a,b) a##b
  #define ASSERT_CONCAT(a,b) ASSERT_CONCAT_(a,b)
  #ifdef __COUNTER__
    #define static_assert(e,m) enum { ASSERT_CONCAT(static_assert_,__COUNTER__) = 1/(!!(e)) }
  #else
    #define static_assert(e,m) enum { ASSERT_CONCAT(assert_line_,__LINE__) = 1/(!!(e)) }
  #endif
  */
#endif

#endif // HELPERS_H
