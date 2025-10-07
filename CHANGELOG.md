# CHANGELOG


## Unreleased

### Bug Fixes

- Fix bug where app would run in debugging mode even when not compiled
  ([`7e4d42f`](https://github.com/kaneryu/Clarity/commit/7e4d42f2715246c899084100fae4fefc277f00ca))

- Fix bug where run.py and main.py still used the old (broken) method to detect if they're compiled
  ([`f639484`](https://github.com/kaneryu/Clarity/commit/f639484fbe2962b80234d523c73913268d906ab0))

- Fix bug where Vlc would always be loaded first regardless of user's choice
  ([`f8f05f6`](https://github.com/kaneryu/Clarity/commit/f8f05f6df45ede764b389952acfb93a4b2433c20))

- Fix bug where workers would be started up twice
  ([`fc84e28`](https://github.com/kaneryu/Clarity/commit/fc84e281a758d622475f56c12c364c3644cc82a4))

- Refactor presence management and improve status handling
  ([`b3505b3`](https://github.com/kaneryu/Clarity/commit/b3505b37e2e1d7c86901ac133d8f0f0ef312aed0))

- Update type annotations for bgworker and asyncBgworker variables
  ([`6ad3d51`](https://github.com/kaneryu/Clarity/commit/6ad3d510bbf24306894fc3825eac84047383525e))

### Chores

- Re-enable git hooks for local version updates
  ([`0fa3ff4`](https://github.com/kaneryu/Clarity/commit/0fa3ff42a95f5f87068d457b084f095007830e88))

### Continuous Integration

- Migrate to python-semantic-release for automated versioning
  ([`e4d729f`](https://github.com/kaneryu/Clarity/commit/e4d729fa2a49ea4b0904182bca4d84ff0c0099c0))

### Features

- Add version.py, contains version information. Also add Release information
  ([`68dc98b`](https://github.com/kaneryu/Clarity/commit/68dc98b8c72bd0335f3cb95572d5c626cc11f1f1))

- Display the current song title and playing status in window title
  ([`c6b49a6`](https://github.com/kaneryu/Clarity/commit/c6b49a6825c5387eb23c980bed790af3111bd136))


## v0.47.3 (2025-10-04)

### Bug Fixes

- Allow album type to include singles in _set_info validation
  ([`7d5f3dd`](https://github.com/kaneryu/Clarity/commit/7d5f3ddeb31496acf9af0f800c490b044e36f357))

- Don't spam online checks when we're offline
  ([`813457c`](https://github.com/kaneryu/Clarity/commit/813457cf2fb12bd58f65d0a2bee1c9f12c2ef433))

- Ensure multiple instances of interval tasks can't be started at the same time
  ([`ea509ba`](https://github.com/kaneryu/Clarity/commit/ea509baa6648f09e68e27ba802addf08323f6381))

- Improvements to notifying logs
  ([`0c1c84c`](https://github.com/kaneryu/Clarity/commit/0c1c84cf90d937255ca8485e276f7d3ea195aa4b))

- Made it so the albumtype is displayed in UI
  ([`f2ded95`](https://github.com/kaneryu/Clarity/commit/f2ded955ccac17d560e1e4deb65f18d3932e3109))

- Update _set_info validation to include EP type
  ([`1caf955`](https://github.com/kaneryu/Clarity/commit/1caf9555456c00b55a3413084f3e26123c8c5af1))

- **navigation**: Add Qt signals and proper change notifications to AppUrl
  ([`9d8f9b4`](https://github.com/kaneryu/Clarity/commit/9d8f9b4f9a0e561cd6ef4990f50aecd02677d797))

### Chores

- Clean up commit 0c1c84
  ([`011f37a`](https://github.com/kaneryu/Clarity/commit/011f37afae851205e61dec2ab455d60e22ab2ecc))

- Remove some debug code
  ([`e6b3697`](https://github.com/kaneryu/Clarity/commit/e6b3697ad153cb73acdcdcad3bff7416e8cb12c4))

- Remove unused hatch requirement
  ([`eb2eac7`](https://github.com/kaneryu/Clarity/commit/eb2eac7796cb0821732974549569f152b0052777))

- Update developer tooling and gitignore
  ([`ba50ca7`](https://github.com/kaneryu/Clarity/commit/ba50ca7feaa0a67b5e2bc392f437d84a46422a66))

### Documentation

- Update README to include instructions for enabling MPV backend during development
  ([`f2676d0`](https://github.com/kaneryu/Clarity/commit/f2676d0a2a80f8f8d88192e4ba924813ceca66f7))

### Features

- Add Albums. Currently available in search.
  ([`659871a`](https://github.com/kaneryu/Clarity/commit/659871a1ebcb8c310630de57dedf6294b770abe2))

- Add occasional task management to BackgroundWorker for dynamic interval tasks, Added occasional
  offlinecheck and occasional discord recconect attempts (closes: 13)
  ([`179f846`](https://github.com/kaneryu/Clarity/commit/179f846573af9c3fce9b9e70d4e565f23071d6cd))

- Add support for multiple media player backends; Implement FFPlay Backend
  ([`847684d`](https://github.com/kaneryu/Clarity/commit/847684d60bfacf121dcd673f11e8f34669c96240))

- Implement multiple media player backends
  ([`d45c2bb`](https://github.com/kaneryu/Clarity/commit/d45c2bb5ad8b333d4f5c84dc1fff8f17191a0820))

- **album**: Add album page with SongListModel and SongProxyListModel
  ([`cef9689`](https://github.com/kaneryu/Clarity/commit/cef96897f629fb48485c6e8ae4d26b1bc30c5675))

- **player**: Standardize MediaPlayer with NAME constant and songChanged(int) signal
  ([`fb66f76`](https://github.com/kaneryu/Clarity/commit/fb66f7628f2a65a537d4ed5630cc91d80c34f83c))

- **queue**: Add async song insertion, goto/gotoOrAdd, and improve player backend fallback
  ([`a6e7f98`](https://github.com/kaneryu/Clarity/commit/a6e7f98a24aaca55fe25b359c9e1f3fc89276a49))

- **song**: Rename downloaded to downloadState and improve initialization
  ([`f3f1295`](https://github.com/kaneryu/Clarity/commit/f3f12958d7928996bd4eead134cc0b94c0bc31bf))

- **ui**: Improve QML components with particles, blur effects, and visual feedback
  ([`1ad6b87`](https://github.com/kaneryu/Clarity/commit/1ad6b87d086beeb47f5e4d6043f4aa3d302b9223))

- **workers**: Add configurable starting interval for dynamic interval tasks
  ([`3a26907`](https://github.com/kaneryu/Clarity/commit/3a26907d7483b5bc38c1af50704a33fd536136c6))

### Refactoring

- **enums**: Change DataStatus from Enum to IntEnum
  ([`e770086`](https://github.com/kaneryu/Clarity/commit/e770086997e2e7a8b7c84751a90f2f13f23e0842))

- **playback**: Remove FFPlayPlayer
  ([`bc45ca0`](https://github.com/kaneryu/Clarity/commit/bc45ca0b4c63673c9a7acd5c63c00fff9d6853e3))

- **search**: Move search() to Interactions and reset model before new search
  ([`42d505a`](https://github.com/kaneryu/Clarity/commit/42d505a304c360057210bc66bc3c130f8c908f50))

- **settings**: Streamline signal connections and improve file handling
  ([`64eed79`](https://github.com/kaneryu/Clarity/commit/64eed79c800b15cb99ee8b64b8772124caaa8ec9))

- **tests**: Simplify CacheManager tests by removing async calls
  ([`3e78011`](https://github.com/kaneryu/Clarity/commit/3e7801125d31065fd637d28cf70a933520d15262))

- **versioning**: Consolidate and improve autover and autochangelog scripts
  ([`b13432b`](https://github.com/kaneryu/Clarity/commit/b13432b2b2b98178175e548e68ffe6faee4c6659))


## v0.37.6 (2025-09-14)

### Bug Fixes

- Add ability for downloader to retry downloading song if chunking doesn't work
  ([`14e7909`](https://github.com/kaneryu/Clarity/commit/14e790914b300347dbcacfbcaa7b1d0796bb03ce))

- Add active song playing check
  ([`695672a`](https://github.com/kaneryu/Clarity/commit/695672a65a85915125ade4611ce50f90023e27f2))

- Add error catching for search, and add hot reload plugin for development
  ([`889937e`](https://github.com/kaneryu/Clarity/commit/889937eb406f22e50c58510c4a6433bef20b794f))

- Add mouseblocker on queue view so clicks and scrolls don't pass through it
  ([`fcb0641`](https://github.com/kaneryu/Clarity/commit/fcb0641ad3c4ff13eb33f670d2d57222b5ba9dd5))

- Add ratelimit to discord presence
  ([`ef913a3`](https://github.com/kaneryu/Clarity/commit/ef913a3d8cb9682db9a3c8ff0c43bdf4b484f653))

- Add some extra resiliency to search
  ([`f283ec2`](https://github.com/kaneryu/Clarity/commit/f283ec253fee145f71ec6553c56fd6fbb963932a))

- Add some things to cleanup
  ([`9526b27`](https://github.com/kaneryu/Clarity/commit/9526b27ce507ee98a707679c004dd81027ac02f7))

- Allow for use of video as a playback MRL
  ([`3415439`](https://github.com/kaneryu/Clarity/commit/3415439b276de1501d34e68715ce6dadd8fa41b3))

- Bug in cacheManager that didn't use asyncio.lock on deleting a key, and also integrity check
  having incorrect implementation.
  ([`4b796fe`](https://github.com/kaneryu/Clarity/commit/4b796fea17c8a6986e2b7c2834782c93f6939c48))

- Bug where incorrect offline check led to infinite recursion
  ([`2f73216`](https://github.com/kaneryu/Clarity/commit/2f73216bb901d40d0be52a7a20c8a97a287e91ec))

- Bug where search used the wrong ID in searchpress
  ([`fe922ae`](https://github.com/kaneryu/Clarity/commit/fe922aec4fe0e205d4e70574b2ebc8ad3043e060))

- Bump dependencies, swap out ytmusicapi for my own version (still async)
  ([`58aae68`](https://github.com/kaneryu/Clarity/commit/58aae689b458947db62d3176164aa6c49cb69d28))

- Codebase now passes mypy check (not in strict mode, with some changes made in mypy.ini)
  ([`1e08f1c`](https://github.com/kaneryu/Clarity/commit/1e08f1c19ce4846c4700edc519f1f0103e22fbf0))

- Decrease offline mode timeout check for faster offline startup
  ([`732248a`](https://github.com/kaneryu/Clarity/commit/732248a8c091050f1c223d26b2963ad642f315d1))

- Emit endReached signal immediately on song finish instead of using QTimer
  ([`17a6887`](https://github.com/kaneryu/Clarity/commit/17a6887542c6a900fb8bfa36157c17698d6052ef))

- Fix bug in cachemanger caused by using async lock in non-async functions
  ([`aadb42b`](https://github.com/kaneryu/Clarity/commit/aadb42b50dab23f87b90bdf664a6821c8d4aff47))

- Fix bug in kimage that wouldn't initialize a variable before downlading the image
  ([`2557b04`](https://github.com/kaneryu/Clarity/commit/2557b043a10f249b639272717bad2a8b1cedd88f))

- Fix bug in song where playback info was never downloaded in the first place
  ([`28f4b93`](https://github.com/kaneryu/Clarity/commit/28f4b93f07b1673226dc6dc6275fe6de05b5239b))

- Fix bug in workers that didn't call the callback if using putcoverconvert, and fix bug that didn't
  convert coverconvert key into path before returing it to the UI
  ([`f7adf6e`](https://github.com/kaneryu/Clarity/commit/f7adf6e3cc8402772fa044adcb9e4286fa2c28a2))

- Fix bug where going to the next song would hang the application; also improve job handling in
  background workers & split queue class up for easier managment
  ([`8a30248`](https://github.com/kaneryu/Clarity/commit/8a30248c46d74e6c64c2d2abc08d82b43a1fd2b7))

- Fix bug where non-rounded cover would be returned when retrieveing cover from cache
  ([`191dbaf`](https://github.com/kaneryu/Clarity/commit/191dbafba0010101f30e649ba725c592b7466c1e))

- Fix bug where notifying log model wouldn't add logs based on error level, and disable song
  fetching if we're offline
  ([`9a680ea`](https://github.com/kaneryu/Clarity/commit/9a680eace74fc8fd672b63c87db22c02157f70d2))

- Fix bug where orphaned items would never actually be deleted in intergrity check
  ([`c131c97`](https://github.com/kaneryu/Clarity/commit/c131c97d8651c93d7b721976bfd3737c88ae918e))

- Fix bug where settings would not save to disk
  ([`d4e973f`](https://github.com/kaneryu/Clarity/commit/d4e973faa8024f2fcce965329858f7d71b69a92f))

- Fix bug where status wasn't updated when fetching image from cache
  ([`984b6ac`](https://github.com/kaneryu/Clarity/commit/984b6acdd9cae01ac6f72392862625a2a873c30b))

- Fix various bugs in cacheManager, while working on the Song tile
  ([`a87caa9`](https://github.com/kaneryu/Clarity/commit/a87caa9eba29e22403934de70e7ea0088396100c))

- Fixed a few startup bugs, made queueview use the Song object
  ([`c74751b`](https://github.com/kaneryu/Clarity/commit/c74751bbbf6cfdb938c6bb944585a09219eecfe0))

- If expiration isn't set, ignore it
  ([`41aafc2`](https://github.com/kaneryu/Clarity/commit/41aafc238d5f7e30c46714b30293160be5fb2999))

- Made duration available from song object
  ([`bdd4a41`](https://github.com/kaneryu/Clarity/commit/bdd4a41a5b27eaa4d3609e9ca2e639a9ca5f3d49))

- Make presence use artist instead of song title
  ([`d9fee30`](https://github.com/kaneryu/Clarity/commit/d9fee3055d69355d68624ccd129af51b4e78ccc2))

- Make progressbar a bit larger
  ([`ddbcdd9`](https://github.com/kaneryu/Clarity/commit/ddbcdd9c4684cbdb2317a5bf78137beb23f7f6e2))

- Make search use the default song thing
  ([`d59c30c`](https://github.com/kaneryu/Clarity/commit/d59c30c412bb7318246d57b3228e6e5bc2ea89ff))

- Make sure presence is stopped and the thread is properly deleted when the app is closed
  ([`f2bc0f1`](https://github.com/kaneryu/Clarity/commit/f2bc0f1da229c7ed300600aa3d063eea9c5caace))

- Make various bugfixes so the app now compiles again
  ([`4e384fb`](https://github.com/kaneryu/Clarity/commit/4e384fb633fccbb6ac4868207153d4be6c3064f7))

- Move default settings out of code, and make sure that the active settings file updates itself to
  the default setting's file schema
  ([`7853cb0`](https://github.com/kaneryu/Clarity/commit/7853cb054dee90588fc842e815dd0f075e29fbea))

- Remove KImage (closes #4)
  ([`7e5ba16`](https://github.com/kaneryu/Clarity/commit/7e5ba16f863924fbf13499d0468a805d005530f1))

- Remove kimage from interactions
  ([`65528e2`](https://github.com/kaneryu/Clarity/commit/65528e22040f9091c5ddb5b979fc41612c960162))

- Skipping forwards in progressbar not functioning
  ([`f8e7077`](https://github.com/kaneryu/Clarity/commit/f8e707725dd5b06e890f55c133dd308adde3f7dd))

- Songs can now be in the queue without a MRL ready
  ([`c84764b`](https://github.com/kaneryu/Clarity/commit/c84764b7b7cc4a7190f121860c5117b4076cb654))

- Update path constants to use uppercase naming convention and add online status management in
  NetworkManager
  ([`a9942e6`](https://github.com/kaneryu/Clarity/commit/a9942e60a83658c442bffb4378f4659a878e9ab1))

- Update search function to allow None as a filter, add copilot Instructions
  ([`9c89287`](https://github.com/kaneryu/Clarity/commit/9c892877dee23b61b8c7027aa89ac4ed29922b81))

- Use logging in both datastore and cache, and make cache more resilient to being moved.
  ([`352ecb0`](https://github.com/kaneryu/Clarity/commit/352ecb02c6f972287c4176e93056ef4173d2adc3))

### Chores

- Add .idea/ to gitignore
  ([`5ecfd02`](https://github.com/kaneryu/Clarity/commit/5ecfd021bf7a9a9cd260103a282ae5357afb3f05))

- Cleanup
  ([`5aae1f7`](https://github.com/kaneryu/Clarity/commit/5aae1f74fb57a902782a1ecab94466d8c2c6f36e))

- Consolidate dependencies into pyproject.toml and remove requirements.txt
  ([`f9fe692`](https://github.com/kaneryu/Clarity/commit/f9fe6929dc9a97d5fc5daf817474ea7ded57289f))

- Remove diabled line in run.py
  ([`1f1abf5`](https://github.com/kaneryu/Clarity/commit/1f1abf5dac0a2be1b2117f701da458c2b184f145))

- Remove some debug prints
  ([`6e45aa6`](https://github.com/kaneryu/Clarity/commit/6e45aa6eee8289232938cbc1ccf7d57142444227))

- Remove some logging from interactions
  ([`6d89fc5`](https://github.com/kaneryu/Clarity/commit/6d89fc5965ba1b89b872968726c397de651a1044))

- Remove some misc prints
  ([`b4c104d`](https://github.com/kaneryu/Clarity/commit/b4c104d82e357b9cfeffd7a79c1b5db3ea9cc2ec))

- Rename
  ([`8b39826`](https://github.com/kaneryu/Clarity/commit/8b39826d7f35a5385c283fc919a7ca4aa92af193))

- Seperate song and queue into seperate files
  ([`f18979d`](https://github.com/kaneryu/Clarity/commit/f18979dac1cb397ede0a366ed20cb2cd27483e5e))

- Some refactoring
  ([`8989d0b`](https://github.com/kaneryu/Clarity/commit/8989d0bd3d433ecd6b465ad1b860707b082bf417))

- Split queue and player
  ([`2e2da0d`](https://github.com/kaneryu/Clarity/commit/2e2da0d0a19659e1fcb9c83fecc93bbb504fe7cf))

- Update actions and gitignore
  ([`567d517`](https://github.com/kaneryu/Clarity/commit/567d51784b8fc4de311e51a01990e89349036408))

- Update actions and gitignore
  ([`e7b1e3d`](https://github.com/kaneryu/Clarity/commit/e7b1e3d9461e8d455071be8ea23d673b87367b12))

- Update gitignore to not include sensitive info.
  ([`afcaf55`](https://github.com/kaneryu/Clarity/commit/afcaf55f979693f923f9b2516d2bf156c28fc6d7))

- Update post-commit to fix pyproject too
  ([`91f93de`](https://github.com/kaneryu/Clarity/commit/91f93de65afdb039dbf274d53e44ce78ad7a4147))

### Features

- Add basic integration with windows SMTC
  ([`76eb732`](https://github.com/kaneryu/Clarity/commit/76eb73260cbe996d8b09763aeccff9a80cb6da6f))

- Add dynamic color based on current song cover
  ([`65b04cc`](https://github.com/kaneryu/Clarity/commit/65b04cce0ae26f908d09bf902837103c51c5441f))

- Add functioning marquee to text elements
  ([`3f6e2a7`](https://github.com/kaneryu/Clarity/commit/3f6e2a768b08c2c4c6b1ed8fcc46402d1d14a280))

- Add new discord RPC feature
  ([`7b470c8`](https://github.com/kaneryu/Clarity/commit/7b470c8e1800de432215b2a7afc031ddf9041719))

- Add settings page
  ([`c73a5f2`](https://github.com/kaneryu/Clarity/commit/c73a5f238a46ec0c5275394111aa69085976e86f))

- Add song image provider, to start moving away from KImage
  ([#4](https://github.com/kaneryu/Clarity/pull/4),
  [`e25e73b`](https://github.com/kaneryu/Clarity/commit/e25e73b4e2a65dc65332870e8e03c249a8ee4ccb))

- Added base for settings
  ([`3cff250`](https://github.com/kaneryu/Clarity/commit/3cff25096d359aa3014bd8b0c1490f8e97bdd6c6))

- Added busyindicators to image to show when the image is loading
  ([`627b786`](https://github.com/kaneryu/Clarity/commit/627b7867aeb4ee062d1f55b9abb5417afca857a0))

- Assosiate song kimages with songs #3
  ([`7f5ff7e`](https://github.com/kaneryu/Clarity/commit/7f5ff7ed14f8bb2cb22977d5d9b887429d62ca33))

- Begin work on login
  ([`fb38983`](https://github.com/kaneryu/Clarity/commit/fb3898373c3dc7b20a8bfbb1708323d80d8a01db))

- Implement dataStore integrity restoration in integrityCheck method
  ([`3addfbc`](https://github.com/kaneryu/Clarity/commit/3addfbc379113c3931e364d5815b97b0a619f9f3))

- Implement debounce logic for Next and Prev song controls
  ([`cd7e027`](https://github.com/kaneryu/Clarity/commit/cd7e02715591c77d52b23f9b12bd2ea98002d22f))

- Implement logging system with notification support and structured log history
  ([`ae12027`](https://github.com/kaneryu/Clarity/commit/ae120273366f856450ca8c75a868e9fe8b9dffda))

- Implement part of reworked networking
  ([`59c67cf`](https://github.com/kaneryu/Clarity/commit/59c67cfb54d45f5e4c571ac0d2ebdc82e83195ff))

- Improve queueview visuals
  ([`2cf1821`](https://github.com/kaneryu/Clarity/commit/2cf1821fed8139030e495b7119b9b228f8f865af))

- Intergrate with winsmtc play, pause, next and prev buttons
  ([`b0965fc`](https://github.com/kaneryu/Clarity/commit/b0965fc4834f509ff0b3b872b0b44358689c28f3))

- **discotube**: Add rich presence support
  ([`74ce8c3`](https://github.com/kaneryu/Clarity/commit/74ce8c3900524ce4522db55c7b59edb2a09585dd))

### Refactoring

- Reorganize imports and move enumerations to dedicated files for better structure
  ([`8c55b58`](https://github.com/kaneryu/Clarity/commit/8c55b58190318f4e38bd559a085a942c83ef21ab))


## v0.20.0 (2025-01-26)

### Bug Fixes

- Add mutexes to increase thread safety
  ([`8dccca2`](https://github.com/kaneryu/Clarity/commit/8dccca2f65d641c8c6f423827cf82c53d69fa679))

- Added fault tolerance to convertocover by making sure that cache is always set to a real cache
  instead of None
  ([`b9de236`](https://github.com/kaneryu/Clarity/commit/b9de23630cc87684098004564392f788e6989a71))

- Fix bug where seeking would cause the play button to show buffering indef
  ([`ea6df18`](https://github.com/kaneryu/Clarity/commit/ea6df180a0dfb73a1a2cf43ed67384901938ce8b))

- Fix bug where songs could not be played if the download was corrupted
  ([`4c7d0ed`](https://github.com/kaneryu/Clarity/commit/4c7d0ed578102577c4ba94252cd08f093e041e88))

- Fix multiple bugs related to downloading songs
  ([`825480e`](https://github.com/kaneryu/Clarity/commit/825480ec3976a121bfa893dc8dbd49b5aa7c7088))

- Fix None in coverconvert caused by imageCache being set too early
  ([`9cf9976`](https://github.com/kaneryu/Clarity/commit/9cf99762eb4b3409ba4900f1bc0d0c7b664dc37a))

- Fix searchModel returning KImage living in different thread
  ([`15f932b`](https://github.com/kaneryu/Clarity/commit/15f932b0de9d2081650f0cb9760214947527cc90))

- Fix spacing and icon height
  ([`ddc86e7`](https://github.com/kaneryu/Clarity/commit/ddc86e784ae39e1252b313c2f68f5a9140c6f42d))

- Fix title in queue, fix overlapping issue in song results
  ([`3ffda25`](https://github.com/kaneryu/Clarity/commit/3ffda2587e890dddbed6ac0a36efbca4e3e25106))

- Song duration not updating
  ([`47673d9`](https://github.com/kaneryu/Clarity/commit/47673d99e9ca16d4cad700d40a3ee93bac58a5d4))

- Speed up setqueue by a bit
  ([`79a6945`](https://github.com/kaneryu/Clarity/commit/79a6945cac5a35ec0113fcd7539e65af5659f3c4))

- Try a fix for no corner radius showing in the songbar image
  ([`a54b8ee`](https://github.com/kaneryu/Clarity/commit/a54b8ee8282cf5b42d8e27159f2fd190cd1af9b8))

- Try another fix for random application crashes because trying to access Song in different thread
  ([`0a5c03d`](https://github.com/kaneryu/Clarity/commit/0a5c03d80dcc68ed662f4ca4b529342aacbd38df))

- Yet another try to fix random application crashes, using an interface to access KImage living in
  different thread
  ([`28d4561`](https://github.com/kaneryu/Clarity/commit/28d4561791055d3b5604f9622959fb3e524f1fab))

- **qml, interactions, song**: Fix random application crash by not directly accessing song object
  that lives in a different thread using QML.
  ([`f62cd6c`](https://github.com/kaneryu/Clarity/commit/f62cd6c40e28f35e32355dd66c7f52151af6a3f4))

- **song, queue**: Added fault tolerance to the queue by allowing it to ask for a song's data to be
  refetched.
  ([`76e2f49`](https://github.com/kaneryu/Clarity/commit/76e2f49375e342fb86a16f1901dc4a6c8ed5ce1f))

- **UI, song, interactions, interfaces**: Fix bug where QML didn't recive the song object properly
  ([`c15f31d`](https://github.com/kaneryu/Clarity/commit/c15f31ded4544eeda63b5ac62df9dc66585ba480))

### Chores

- Add new workflow
  ([`192dd64`](https://github.com/kaneryu/Clarity/commit/192dd645d888ad4b273268988e469017d6e0a1a5))

- Added an alternate way to bump the version in autover
  ([`a3e203c`](https://github.com/kaneryu/Clarity/commit/a3e203ca186a3fac561dec189dd8cef8fccd94bf))

- Added downloaded songs to debug queue
  ([`f9b3efe`](https://github.com/kaneryu/Clarity/commit/f9b3efe759303552797c7ff067bef092cdb315a9))

- Copy over autochangelog from dev branch
  ([`bd509b5`](https://github.com/kaneryu/Clarity/commit/bd509b54c906286053a4c6c4b951b6ed701950dd))

- Copy over commit hooks from dev branch
  ([`1b71ae2`](https://github.com/kaneryu/Clarity/commit/1b71ae2931434f26dabac6498540016e566b5cab))

- Fix bug in hooks caused by move
  ([`b5aad73`](https://github.com/kaneryu/Clarity/commit/b5aad7317e4e761fc6f4ec49b185e9b29a2630d2))

- Re-lock dependencies, add the new dependencies
  ([`42d22ef`](https://github.com/kaneryu/Clarity/commit/42d22ef7d5acc37a98b24f8f21e55b8fdcaf3d59))

- Update workflow
  ([`2ea0baa`](https://github.com/kaneryu/Clarity/commit/2ea0baa9183e4ea14ef0fe6d3cdfab53e37f859b))

- **build**: Update action to only run on push to main branch
  ([`26ca202`](https://github.com/kaneryu/Clarity/commit/26ca202865e1f431a5c1967c9eb536bf4dfde4d4))

### Features

- Add font files to the application with a test on the homepage
  ([`bab8d00`](https://github.com/kaneryu/Clarity/commit/bab8d0009c15b8524e4ba107a0a33fb18091fab9))

- Add functionality to the queueview
  ([`bc8b687`](https://github.com/kaneryu/Clarity/commit/bc8b6874b2925ef0e9cda9e91f1802e89e1e43b2))

- Add prerequisite for queuePanel
  ([`e66e1a5`](https://github.com/kaneryu/Clarity/commit/e66e1a5f37b6960fcbe34145d27311299f9dcc24))

- Improve semantics around the play/pasue button, and fix a bug where it wouldn't update sometimes
  ([`1fe292b`](https://github.com/kaneryu/Clarity/commit/1fe292bd03034e17fbbb39428d30ebd01f7c4bfc))

- Replace placeholder text on songbar to be icons
  ([`6ede0c4`](https://github.com/kaneryu/Clarity/commit/6ede0c45b1d5d17d4f4d867058d72118fbe74d54))

- **song**: Song no longer downloads playback info from internet if it's already downloaded
  ([`c73af7c`](https://github.com/kaneryu/Clarity/commit/c73af7cae610addc158024f01ff538277d99e251))

- **song, download**: Add song downloading
  ([`4b6d0b8`](https://github.com/kaneryu/Clarity/commit/4b6d0b807c04528f238c3cc8f7dae01a047ba5d7))

- **songBar**: Added song cover, song details to the songbar
  ([`b7467aa`](https://github.com/kaneryu/Clarity/commit/b7467aae66eb42fe5f61b693f8565962528440e6))

- **songbar**: Complete alpha songbar
  ([`7cdc978`](https://github.com/kaneryu/Clarity/commit/7cdc978feb15d548213b541e1299fba53a72bdbc))

- **songbar, bgworkers**: Improve songbar, add threading to non-async bgworker, refactor some stuff
  ([`655da11`](https://github.com/kaneryu/Clarity/commit/655da11de10990e76f98c678248b20d2df245ae9))

### Refactoring

- Fix some code, add phanthomjs, add material symbols
  ([`0551a78`](https://github.com/kaneryu/Clarity/commit/0551a78ebcba08023abb0dd03879a4cd133b487c))

- Remove some debugging code
  ([`a16bab8`](https://github.com/kaneryu/Clarity/commit/a16bab8520eefdc90561b5c814b71a11ff6abad7))

- Remove some print statements
  ([`ef2b5a8`](https://github.com/kaneryu/Clarity/commit/ef2b5a8409903419fad26694318405cba7b13b27))

- Remove some print statements
  ([`eddb39c`](https://github.com/kaneryu/Clarity/commit/eddb39c65944c50ed7480e824a4852a50006dd8f))

- **cache**: Make cache non-async
  ([`70bfb0a`](https://github.com/kaneryu/Clarity/commit/70bfb0a8c3b55c5a21c7d7478de99d808200bde9))

- **queue, song**: Combine queue and song classes into one file
  ([`d9cf0a4`](https://github.com/kaneryu/Clarity/commit/d9cf0a4ec045d90edcbd00e593ed91d6c8ea368e))

- **song**: Remove some debugging code
  ([`392a89e`](https://github.com/kaneryu/Clarity/commit/392a89e823a119b288f932b1cecb89b1b5c881fc))


## v0.10.0 (2025-01-25)

### Bug Fixes

- Made sure gitignore ignores cache files
  ([`ea93fe2`](https://github.com/kaneryu/Clarity/commit/ea93fe234208c1d70cdb6a428ca4811ad16444da))

- **action, build**: Move yt_dlp fix (occured in untracked file, involved deleting a bunch of code)
  into a config.yaml. Also included proper dependencies in the requirements.txt for the aciton.
  ([`73d0526`](https://github.com/kaneryu/Clarity/commit/73d0526e9144b5db27fa33b625176bbf9bbe0450))

- **actions**: Update action
  ([`63509e6`](https://github.com/kaneryu/Clarity/commit/63509e69bc4f9fe812fac125913f8c8e10a57947))

- **actions**: Windows only
  ([`f879ccd`](https://github.com/kaneryu/Clarity/commit/f879ccdcc1744837a8102579741e2dc2506dba94))

- **autover**: Clean up autover.py for use in commit hooks
  ([`5f9f383`](https://github.com/kaneryu/Clarity/commit/5f9f383320af0775a42cba37d31ef80b2fd571c5))

- **autover**: Fix bug in autover where commit history was reversed.
  ([`99a2d6b`](https://github.com/kaneryu/Clarity/commit/99a2d6b2f0c716fd49141cf68c0e9731fd1a5630))

- **build**: Add versions as datafiles, add app icon to app.
  ([`8a3c4fd`](https://github.com/kaneryu/Clarity/commit/8a3c4fddf7db6ecf2f5102866997d2d3810cde94))

- **build**: Switched from using --standalone to --mode=app
  ([`8b88c35`](https://github.com/kaneryu/Clarity/commit/8b88c354abf8d333a12a4d211524aaad3be6dadd))

- **build**: Update run.py
  ([`fc72bdd`](https://github.com/kaneryu/Clarity/commit/fc72bddbe50478624218b5ba757d2aaa808271af))

- **cache**: Make cache more resistant when data is deleted but the reference is not
  ([`1b5eec2`](https://github.com/kaneryu/Clarity/commit/1b5eec22418af64b216381e11dd209333ed5b475))

- **freezing**: Make some changes to make freezing via nuitka work, and add the configuration to
  run.py
  ([`a036182`](https://github.com/kaneryu/Clarity/commit/a0361824b6bdca971e3a109871365104f11d2e26))

- **queue**: Fix issues caused queue module having a name conflict
  ([`f09b4f1`](https://github.com/kaneryu/Clarity/commit/f09b4f110026434f6594ac620507a8b714403ea4))

- **version**: Fix version file not being found causing application crash
  ([`1160727`](https://github.com/kaneryu/Clarity/commit/11607275346e97179698f7b92b87ecf4d14c4cb8))

### Chores

- Edit.gitignore
  ([`5602779`](https://github.com/kaneryu/Clarity/commit/560277990b79aeda445b49270773f9e977fde871))

- Fix for no tag
  ([`b38396b`](https://github.com/kaneryu/Clarity/commit/b38396b3dc2466bbbb96ee0977da7a41444f3744))

- Remove build script, auto-create releases
  ([`a12992f`](https://github.com/kaneryu/Clarity/commit/a12992fbbd6265e773f0bd2fad937296ab08ab8b))

- Undo last commit
  ([`3c5da9a`](https://github.com/kaneryu/Clarity/commit/3c5da9a6c63dac82f4b80330ebd813642fa1c029))

- **build**: Added caching to dependencies
  ([`0a2b72b`](https://github.com/kaneryu/Clarity/commit/0a2b72b4fae75409b4426a82e68015534c9021f6))

- **build**: Decided to remove file version from build config
  ([`db2c882`](https://github.com/kaneryu/Clarity/commit/db2c88239ce4673a6171a193268b69c0e9f36cc8))

- **build**: Remove anti-bloat from pluginlist
  ([`961082b`](https://github.com/kaneryu/Clarity/commit/961082b303a92df3e4e06c839d2f16baef04238d))

- **queue**: Remove old queue file
  ([`50186e3`](https://github.com/kaneryu/Clarity/commit/50186e320b1472a4ec8998431a229538daecff55))

### Features

- **actions**: Add requirements so workflow functions
  ([`070b9b5`](https://github.com/kaneryu/Clarity/commit/070b9b5a31ebaf049476bb4c488784649f4c0f49))

- **autover**: Added autoversioning using conventional commits
  ([`34a5ca2`](https://github.com/kaneryu/Clarity/commit/34a5ca2e03170677d8a8529828826c3a0651ccdb))

- **build**: Try a fix for build failing
  ([`7f2c526`](https://github.com/kaneryu/Clarity/commit/7f2c526915eeda30109beb7a37a9e68af0557038))

- **cache**: Enhance cache integrity checks and cleanup process via new integrityCheck function
  ([`2076b09`](https://github.com/kaneryu/Clarity/commit/2076b09b484a40fb1bf1a38616b4fb72b7eef647))

- **pages, protocol**: Add pages to the app using a URL scheme, with innertune:// as the protocol
  ([`7621cba`](https://github.com/kaneryu/Clarity/commit/7621cba8338d94c3436ae049a032dc73758e40d2))

- **queue, gui**: Added the QueueModel, and connected it to the QML.
  ([`80e346a`](https://github.com/kaneryu/Clarity/commit/80e346a4dbeec28e7af7caa36d8559a038fb99c3))

- **queue, player, gui**: Added the basic queue and player, and made the connection from it to the
  GUI
  ([`ca241a4`](https://github.com/kaneryu/Clarity/commit/ca241a43e9cd5f1c18e15859cd3786b43acce2df))

- **search**: Added images to search results in QML, also refactored a few things to do so.
  ([`fd0a870`](https://github.com/kaneryu/Clarity/commit/fd0a870d01a50175d6e9101e276fcc76f2eea2fb))

- **search**: Added preliminary version of search, and made connection the the UI. it can also play
  songs from the results.
  ([`ad22754`](https://github.com/kaneryu/Clarity/commit/ad2275478444f14ce77a2870c82c78640b84ea22))

- **songbar**: Add prelim stuff for songbar
  ([`fd8bcd4`](https://github.com/kaneryu/Clarity/commit/fd8bcd49ac9bf4ac564487bb6ef0d4d603b3bf7e))


## v0.0.0 (2024-02-03)