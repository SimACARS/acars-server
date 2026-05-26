# Changelog

# [1.3.0](https://github.com/SimACARS/acars-server/compare/v1.2.2...v1.3.0) (2026-05-26)


### Features

* added common functions ([3af47e0](https://github.com/SimACARS/acars-server/commit/3af47e0ef269012b87636065b22fe44fd7a177c3))
* added METAR, TAF and SHORTTAF ([7f3c6ef](https://github.com/SimACARS/acars-server/commit/7f3c6ef1dd3ee16221a2738152d1cefe496bc17b))
* inforeq atis for vatsim ([040797f](https://github.com/SimACARS/acars-server/commit/040797f95e33e0d8ef139eaa0830d910a921bb1d))

## [1.2.2](https://github.com/SimACARS/acars-server/compare/v1.2.1...v1.2.2) (2026-05-26)


### Bug Fixes

* failing on no master key being found ([9462a91](https://github.com/SimACARS/acars-server/commit/9462a91c3e8ca4953dca7d2b1ac112c8e11ddd9a))
* test code left in error ([e6c48b9](https://github.com/SimACARS/acars-server/commit/e6c48b9e8a783a8c156e41bb041f3a9c8a8766f1))

## [1.2.1](https://github.com/SimACARS/acars-server/compare/v1.2.0...v1.2.1) (2026-05-26)


### Bug Fixes

* missing inforeq message type ([d568a00](https://github.com/SimACARS/acars-server/commit/d568a0089264332505e10e22584a99c058ba61c4))

# [1.2.0](https://github.com/SimACARS/acars-server/compare/v1.1.0...v1.2.0) (2026-05-25)


### Bug Fixes

* default of None not allowed in relay fields ([e4c9a1d](https://github.com/SimACARS/acars-server/commit/e4c9a1df9840636b7f427f09c70bb4ee8e6af7c3))
* forgot to move the test code over to prod ([7b34fc2](https://github.com/SimACARS/acars-server/commit/7b34fc21eefcfb850bbaae2961e6088928859cef))
* no exception raised if invalid network is passed ([c7095fb](https://github.com/SimACARS/acars-server/commit/c7095fb0300681a3012a26f6334fda9aab2fbc4b))
* not returning a redirect ([20c8974](https://github.com/SimACARS/acars-server/commit/20c8974a69450faa41a41e72321c7fbfd9fff279))


### Features

* fully working relay ([acaa05d](https://github.com/SimACARS/acars-server/commit/acaa05d314136e9929d596177d773dc98bea6d2d))
* fully working store ([be09047](https://github.com/SimACARS/acars-server/commit/be09047f5e19bf907611a48e1b1228831e49df11))


### Performance Improvements

* moved networks to static data ([392d8bb](https://github.com/SimACARS/acars-server/commit/392d8bbe14f12b54d0a39296bb91a09394689297))
* removed extra print statement ([2cebcfe](https://github.com/SimACARS/acars-server/commit/2cebcfeafb35b396d9f077c32de8383fe19268fa))
* removed unused imports ([#4](https://github.com/SimACARS/acars-server/issues/4)) ([913f009](https://github.com/SimACARS/acars-server/commit/913f00944a0490533100e08d5dbb6d250ee5a226))

# [1.1.0](https://github.com/chssn/acars-server/compare/v1.0.0...v1.1.0) (2026-05-25)


### Bug Fixes

* db create security ([aa9c266](https://github.com/chssn/acars-server/commit/aa9c26635250830d2ca48ad804d2f4364c133052))
* incorrect api key lookup ([d656ec7](https://github.com/chssn/acars-server/commit/d656ec7b67b1c0454760bb0ca1e4e0ae38f6d7de))
* missing fields ([a3cda62](https://github.com/chssn/acars-server/commit/a3cda628732fa2b3c8ca15e37d49924fc31a7758))
* not handling VATSIM OAuth errors correctly ([e4e30f8](https://github.com/chssn/acars-server/commit/e4e30f836fedf7425824c30f7a5a67118b3453cd))


### Features

* added api authentication and sql backend ([795ef5d](https://github.com/chssn/acars-server/commit/795ef5da69f2be4cf76deac18f5fb6ffe2733d2a))
* added lifespan manager ([5e0b1e4](https://github.com/chssn/acars-server/commit/5e0b1e4ce25e7304e1f0b5e512548dab98aa3d05))


### Performance Improvements

* remove unused imports ([298e1f3](https://github.com/chssn/acars-server/commit/298e1f31542f865c57017a4c85076395511ac8ad))

# 1.0.0 (2026-05-25)


### Features

* Authentication Updates ([#2](https://github.com/chssn/acars-server/issues/2)) ([04c7d58](https://github.com/chssn/acars-server/commit/04c7d584e4d1f53056c1fe2d4642cb097179f5a1))
