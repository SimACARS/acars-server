# Changelog

## [1.10.7](https://github.com/SimACARS/acars-server/compare/v1.10.6...v1.10.7) (2026-06-05)


### Bug Fixes

* endpoints should always return json ([f4bef40](https://github.com/SimACARS/acars-server/commit/f4bef40cfcd8d213eba34ea45899129994ee0e52))
* oauth state code not accessed ([ef56b29](https://github.com/SimACARS/acars-server/commit/ef56b29acc4cfba970b6117f4e32dae36d547056))

## [1.10.6](https://github.com/SimACARS/acars-server/compare/v1.10.5...v1.10.6) (2026-06-04)


### Bug Fixes

* adding a record fails ([28d2a8a](https://github.com/SimACARS/acars-server/commit/28d2a8a06d8a92e7af1c273b28a11e0d74575e99))
* airline callsign needs to accept the prefix _COY_ ([18c0430](https://github.com/SimACARS/acars-server/commit/18c043066aa848ff84a5fc9b4f8fbda561a940f5))
* block is too long ([8eed57e](https://github.com/SimACARS/acars-server/commit/8eed57eb2b08a8ea9b313cc46ee9914576e53131))
* continually adding the same group ([fc14a0c](https://github.com/SimACARS/acars-server/commit/fc14a0c6a614272417172cf59b1d502c01efc738))
* doesn't need to be async ([1c141af](https://github.com/SimACARS/acars-server/commit/1c141af3ab5bc1e7c83465a9ef9abafc1ab2d71c))
* fastapi EventSourceResponse and ServerSentEvent aren't playing nicely ([30a88ce](https://github.com/SimACARS/acars-server/commit/30a88ce3638d5604986ae0cbc4a7efee54a6c8aa))
* flushall shouldn't be async ([ab464af](https://github.com/SimACARS/acars-server/commit/ab464af189e5285b075af8495392f682c77f0e89))
* messy code needs tidying ([2c143aa](https://github.com/SimACARS/acars-server/commit/2c143aa7157e1187ebca20eb8d3bffa7e89a7112))
* missing last_used from create ([de9ca42](https://github.com/SimACARS/acars-server/commit/de9ca424233dc7c0f71ff614f217f889c5670913))
* race condition ([a614068](https://github.com/SimACARS/acars-server/commit/a61406847d198adf287d31fba4d1bafc9ccd2e27))
* should be using the async db ([5ca3b57](https://github.com/SimACARS/acars-server/commit/5ca3b575ce261969b27434ab3d5c3066f4f49b79))
* testing the length of the verification token is == 1 which is the wrong thing! ([89801b1](https://github.com/SimACARS/acars-server/commit/89801b1b2e70903cf6974283c25726864dad9864))
* use new RequestNewAirline model ([24b8f62](https://github.com/SimACARS/acars-server/commit/24b8f624d1f21eb0dbfff8a02d52700b178fb552))


### Performance Improvements

* removed if statement which wasn't needed ([36d28a6](https://github.com/SimACARS/acars-server/commit/36d28a652a6496fcf8621c80c69e9057e9a6efca))

## [1.10.5](https://github.com/SimACARS/acars-server/compare/v1.10.4...v1.10.5) (2026-06-04)


### Bug Fixes

* icao no showing for no ATIS ([1da9caa](https://github.com/SimACARS/acars-server/commit/1da9caa3579e3f4751a9a08719a8b90a9147ce60))
* not returning 403 errors ([a4c1fd0](https://github.com/SimACARS/acars-server/commit/a4c1fd0b496beb3e399ca8851106397e685e2f0b))
* raises NotFoundError instead of returning 404 ([c5a789f](https://github.com/SimACARS/acars-server/commit/c5a789fff5fa839c05f97088dbd97e1c7db92dd1))
* response content needs to be clearer ([39a0975](https://github.com/SimACARS/acars-server/commit/39a0975b21c9571793cc81b8daff43de6a18fd34))
* scope is too wide, shouldn't include airline name ([952fda5](https://github.com/SimACARS/acars-server/commit/952fda5b3c9c5008a9f3c958e0148630bca43385))
* vatsim metar returns a blank string if unknown icao ([a64cb2c](https://github.com/SimACARS/acars-server/commit/a64cb2cd968375b8b1e66c957495bafb6080bfa2))


### Performance Improvements

* check not required as already tested in model validation ([ebc119a](https://github.com/SimACARS/acars-server/commit/ebc119a9dc1c127e96c4a65da05b848a80a85d66))
* removed uneccesary if blocks ([7d52748](https://github.com/SimACARS/acars-server/commit/7d527485a268253723ed6bff40721ec85a5ee15c))

## [1.10.4](https://github.com/SimACARS/acars-server/compare/v1.10.3...v1.10.4) (2026-06-03)


### Bug Fixes

* airline authentication isn't correctly raising 401 errors ([5770f49](https://github.com/SimACARS/acars-server/commit/5770f493a419c0c6a38f730481f280175d625ea3))
* failed StoreAndForward validation ([325b5b1](https://github.com/SimACARS/acars-server/commit/325b5b14d8a912d9f4e83028f08bd69bb0b53b29))
* maximum length set too short ([1f422d7](https://github.com/SimACARS/acars-server/commit/1f422d7bc541c2454758d77e78e7b8d0fde44d63))
* should be False NOT 0 ([ba40477](https://github.com/SimACARS/acars-server/commit/ba40477465c0602bfb4c8ddb0989b55d09886cab))
* this shouldn't be a string, needs to validate the None ([a162d50](https://github.com/SimACARS/acars-server/commit/a162d50334921c6779df16678ce7e7effb40969d))


### Performance Improvements

* removed oooi endpoint as currently redundant ([6720bd0](https://github.com/SimACARS/acars-server/commit/6720bd0066c1082421be154ff54b439c663f523f))
* removed redundant code ([44a615a](https://github.com/SimACARS/acars-server/commit/44a615a805be3013e7f01c68f07f31512edc706d))
* removed redundant code ([e6e66bb](https://github.com/SimACARS/acars-server/commit/e6e66bb8f3b0159ad0e2076cc0bd6c6e3b99123a))
* removed test code ([024a2ee](https://github.com/SimACARS/acars-server/commit/024a2eeba26eacbb839607c33564752c2270178f))
* removed unused import ([c71e86a](https://github.com/SimACARS/acars-server/commit/c71e86a759f468b20729edea5b664104448b9ff1))

## [1.10.3](https://github.com/SimACARS/acars-server/compare/v1.10.2...v1.10.3) (2026-06-03)


### Bug Fixes

* incorrect status code - should be 400 ([bc78e6b](https://github.com/SimACARS/acars-server/commit/bc78e6b291fbb8219fd7680ac29e88f8464ff5ce))
* regex is too strict ([4550b90](https://github.com/SimACARS/acars-server/commit/4550b906c5f9963a9cf772eb58b7d3363e84b1fd))

## [1.10.2](https://github.com/SimACARS/acars-server/compare/v1.10.1...v1.10.2) (2026-06-02)


### Bug Fixes

* fails on NotFoundError ([06c2bce](https://github.com/SimACARS/acars-server/commit/06c2bcea98b9776cb94a2ef809093f280669ee91))
* fails on redis NotFoundError ([f76d8d7](https://github.com/SimACARS/acars-server/commit/f76d8d7b61ba2f010a582e3bd2b11ca67b01af03))
* inconsistent startup behaviour ([f70b283](https://github.com/SimACARS/acars-server/commit/f70b2833eee22790e08322f1aa0b1d7fe73e7ea1))
* not returning json string ([313baec](https://github.com/SimACARS/acars-server/commit/313baec81fe4cfbb1641f8f8f9884ca504000a3e))
* searching text when should be tag ([1feb2bd](https://github.com/SimACARS/acars-server/commit/1feb2bda6a184a35ab10347dcc79cb8943e63c5f))
* unable to logoff as an airline ([b7f510f](https://github.com/SimACARS/acars-server/commit/b7f510fd0359fff26f2ae22084838db308cfff9f))
* unvalidated logoff request model ([96a0a44](https://github.com/SimACARS/acars-server/commit/96a0a44c4f9b7871fec71fafcbfdaeb795937175))
* won't accept an airline trigram for logon ([081d358](https://github.com/SimACARS/acars-server/commit/081d3586a28100e94f7b5d82adbc6cadccb98fdd))


### Performance Improvements

* removed test code ([635e066](https://github.com/SimACARS/acars-server/commit/635e0662e0a06d6b8336b086927df2a89b9dddc2))

## [1.10.1](https://github.com/SimACARS/acars-server/compare/v1.10.0...v1.10.1) (2026-06-01)


### Bug Fixes

* awaiting sync function ([71ee6b1](https://github.com/SimACARS/acars-server/commit/71ee6b1cbb08842e53fe430e482f0d8080edc17d))
* message should be commited to sf first ([fa50a8c](https://github.com/SimACARS/acars-server/commit/fa50a8c4dd8ce1d1455408c4d951bffa0940b459))
* redis.exceptions.DataError ([634b0c5](https://github.com/SimACARS/acars-server/commit/634b0c5ae05aed1f0ad1cb4f2b7587e82b62addc))

# [1.10.0](https://github.com/SimACARS/acars-server/compare/v1.9.0...v1.10.0) (2026-06-01)


### Bug Fixes

* ambiguous error message ([bf8f944](https://github.com/SimACARS/acars-server/commit/bf8f944d348332c6b7ee54b413edd4d508c650ab))
* incompatable type ([4e99188](https://github.com/SimACARS/acars-server/commit/4e99188fbca9f18e009b499e8d4201d775a237d4))
* incorrect if statement ([41d734c](https://github.com/SimACARS/acars-server/commit/41d734c1e834e6e42913d2750e6c7928c00eabac))
* missing f string ([cc42825](https://github.com/SimACARS/acars-server/commit/cc42825035d9d3c9b8b6314f5fe578889ac27728))
* no follow on link ([8572b13](https://github.com/SimACARS/acars-server/commit/8572b131e4d602e4917a108201e68dc3fa027efc))
* non-expiring messages ([9b7c1ed](https://github.com/SimACARS/acars-server/commit/9b7c1ed669f77a49a8f056a778d2d62410a616c8))
* should be select one not select all ([7d8af75](https://github.com/SimACARS/acars-server/commit/7d8af7578aa23a0d47a1b16fe31a04dc9ff48de5))
* unable to access key ([e71f270](https://github.com/SimACARS/acars-server/commit/e71f27023173d3456a5592a70e0bd4438727a8d1))
* unable to call get_items ([dc33017](https://github.com/SimACARS/acars-server/commit/dc3301757159173d828a0b6a9cbd6b19389ff1f8))


### Features

* _COY_ prefix for airlines ([e377d9f](https://github.com/SimACARS/acars-server/commit/e377d9f1a9248f60c9c985cf1379ab3790e4d43b))
* airline dlic logon ([3f32b19](https://github.com/SimACARS/acars-server/commit/3f32b194250ff2957f635378da036f1fe20f462e))
* airline domain verification ([2c7bc21](https://github.com/SimACARS/acars-server/commit/2c7bc218bcb3f418ba6385d8046228bfb9d34d83))
* airlines only allowed to send to an online station ([4246b42](https://github.com/SimACARS/acars-server/commit/4246b42a1b6da2d7630a63650a265ffb70182c4a))
* domain authentication ([02c775e](https://github.com/SimACARS/acars-server/commit/02c775e51bd688569982db436c27f5f1a108a9b6))
* globall dlic logoff ([bb45d9a](https://github.com/SimACARS/acars-server/commit/bb45d9a14b18cf7c80223fa082acda407f290dfc))
* use SSE to send events to airlines ([eb8527b](https://github.com/SimACARS/acars-server/commit/eb8527b99058c6df8dbb16b67ec1fd8e8fbc51c2))

# [1.9.0](https://github.com/SimACARS/acars-server/compare/v1.8.0...v1.9.0) (2026-05-31)


### Bug Fixes

* EUROCONTROL-SPEC-107 - 5.1.1.4 - Allowed Characters ([5698302](https://github.com/SimACARS/acars-server/commit/5698302958d9f4bc834952bb802be035a2e034bf))
* network not being validated ([fa5f99d](https://github.com/SimACARS/acars-server/commit/fa5f99d9133365d09d9adbb1253d68cd63f7e570))
* packet should be full text search ([0396c4d](https://github.com/SimACARS/acars-server/commit/0396c4d996f0a507877de1783db7b3333f03c222))
* should be to page 266 ([c2719cf](https://github.com/SimACARS/acars-server/commit/c2719cf2396989239fffec90c294a4abfc4cc680))
* should direct call the subclass ([7d9af9d](https://github.com/SimACARS/acars-server/commit/7d9af9d5910e94d68e082bb04af620972aa5e956))
* some fields not being  indexed ([c8f10be](https://github.com/SimACARS/acars-server/commit/c8f10be729dd02b7342dc3d2b0fb440389a6f183))
* sql should be databases ([9885ed3](https://github.com/SimACARS/acars-server/commit/9885ed36acec9b131b12665015f7b256f740fb83))
* unable to bypass callsign verificatino for testing ([f03e37c](https://github.com/SimACARS/acars-server/commit/f03e37cc0342408574ec69f8e6def0a4aba076aa))


### Features

* ability to add test users ([e71a385](https://github.com/SimACARS/acars-server/commit/e71a38529279d2c244cd17191e34d5bebb8f03b5))
* added rcp standards ([88a80fa](https://github.com/SimACARS/acars-server/commit/88a80fa67d7f63038581b0abc63d222a45bdef54))
* CPDLC downlink messages ([2d43b93](https://github.com/SimACARS/acars-server/commit/2d43b93ad5aa00bdc8a6af5ddddf10b2012cb510))
* CPDLC uplink messages ([79631e2](https://github.com/SimACARS/acars-server/commit/79631e2ed4e36bde02d4247d59f966f5867e5382))
* DLIC logon and logoff ([d826f09](https://github.com/SimACARS/acars-server/commit/d826f09d46b2151815cfc7e70273f6b70076b52f))
* ground and aircraft CPDLC systems ([39e0c18](https://github.com/SimACARS/acars-server/commit/39e0c180dc9f875b3536c196baec9d29d03854d2))
* write cpdlc data to sql db ([80ff99a](https://github.com/SimACARS/acars-server/commit/80ff99a49763b3e174b10a6c6074eeeb25f6052c))


### Performance Improvements

* remove unused import ([b6580a1](https://github.com/SimACARS/acars-server/commit/b6580a1e8a1ee3ea98a8219262e23f98b8d6c4e0))

# [1.8.0](https://github.com/SimACARS/acars-server/compare/v1.7.0...v1.8.0) (2026-05-31)


### Features

* cpdlc message elements and standardized free text messages ([#23](https://github.com/SimACARS/acars-server/issues/23)) ([cf228eb](https://github.com/SimACARS/acars-server/commit/cf228eb56aa7c4eaa9c28018cb30fcb7c7c0d7d4))

# [1.7.0](https://github.com/SimACARS/acars-server/compare/v1.6.2...v1.7.0) (2026-05-30)


### Features

* 19 chore implement opentelemetry openobserve ([#21](https://github.com/SimACARS/acars-server/issues/21)) ([52a8d07](https://github.com/SimACARS/acars-server/commit/52a8d076f570a6b547656c7ababd71d2208a60df))

## [1.6.2](https://github.com/SimACARS/acars-server/compare/v1.6.1...v1.6.2) (2026-05-29)


### Performance Improvements

* removed unused imports ([6d33774](https://github.com/SimACARS/acars-server/commit/6d33774ed3c2b73ebd1c450d10f2abb6e8fa8254))

## [1.6.1](https://github.com/SimACARS/acars-server/compare/v1.6.0...v1.6.1) (2026-05-29)


### Performance Improvements

* removed unused import ([a008699](https://github.com/SimACARS/acars-server/commit/a008699687fcebfac139c44f31065a91f4599cfc))

# [1.6.0](https://github.com/SimACARS/acars-server/compare/v1.5.0...v1.6.0) (2026-05-29)

# [1.5.0](https://github.com/SimACARS/acars-server/compare/v1.4.1...v1.5.0) (2026-05-27)


### Features

* basic logging to a webpage ([bcc2563](https://github.com/SimACARS/acars-server/commit/bcc256361262f3dfcad6574bb9fbcd0635c6aea5))

## [1.4.1](https://github.com/SimACARS/acars-server/compare/v1.4.0...v1.4.1) (2026-05-27)


### Bug Fixes

* ApiKey incorrectly assigned to StoreAndForward ([79ce3cb](https://github.com/SimACARS/acars-server/commit/79ce3cba694eb9bd678d0dfe618acdfb7c2d44d6))


### Performance Improvements

* added more timeouts ([e068552](https://github.com/SimACARS/acars-server/commit/e068552d20b062c0b7d4ea1fe8642af2239ae613))
* added requests timeout ([201d692](https://github.com/SimACARS/acars-server/commit/201d692ea1f5d84f821dfdb437fea9fe0760fc6b))
* removed redundant test functions ([cc712e8](https://github.com/SimACARS/acars-server/commit/cc712e87931506ffd7357cc634a151b780929446))
* removed unused module ([841c229](https://github.com/SimACARS/acars-server/commit/841c229d7bda8988c6105161b5051924d7902219))
* removed unused typing imports ([8a74b6c](https://github.com/SimACARS/acars-server/commit/8a74b6c63484461587f72cfbdacaee1531976a10))

# [1.4.0](https://github.com/SimACARS/acars-server/compare/v1.3.1...v1.4.0) (2026-05-26)


### Bug Fixes

* allow A and D ATIS ([2aeb382](https://github.com/SimACARS/acars-server/commit/2aeb382896cf6ade7be5d2b958317deecb85a77b))
* missing ads-c legacy message type ([a32929a](https://github.com/SimACARS/acars-server/commit/a32929a411f7c49ff7afcd428a5320bde2170088))


### Features

* basic validation of ads-c and cpdlc message types ([d78e304](https://github.com/SimACARS/acars-server/commit/d78e30493a77d125e8cd4a3cf8c90f6603894298))


### Performance Improvements

* removed some code duplication ([0fc5162](https://github.com/SimACARS/acars-server/commit/0fc516240e3d81cb9d49c2f18edf301444c3c0c4))

## [1.3.1](https://github.com/SimACARS/acars-server/compare/v1.3.0...v1.3.1) (2026-05-26)


### Bug Fixes

* this isn't legacy, this is new ([2745534](https://github.com/SimACARS/acars-server/commit/27455347ed73376f872de70e6e0da40c39931931))

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
