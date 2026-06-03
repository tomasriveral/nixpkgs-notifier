# nixpkgs-notifier
A notifiy wrapper on top of https://nixpk.gs/pr-tracker.html

It can send you classic notifications or send a message to a matrix room when a tracker PR is merged into nixos-unstable.

### Install
Add this inputs in your flake.nix
```nix
nixpkgs-notifier = {
  url = "github:tomasriveral/nixpkgs-notifier";
};
```
You can follow the inputs, by adding:
```nix
nixpkgs-notifier = {
  url = "github:tomasriveral/nixpkgs-notifier";
  inputs.flake-utils.follows = "flake-utils";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

You can later reference the package with `inputs.nixpkgs-notifier.packages.${pkgs.system}.default`

If you want to recieve the notification via matrix, run `matrix-commander-rs --login`

### Configuration
Configuration file is in ~/.config/nixpkgs-notifier/config.json
It's created by the program if it doesn't exist.
The default values are below.
```json
{
  "configTime": 3600,
  "configFetchTime": 1,
  "localNotify": true,
  "matrix": {
    "enable": false,
    "room": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "ping": false,
    "userPing": "@someone",
    "userPingServer": "matrix.org"
  }
}
```
`configTime` (seconds) is the time between each check of all the PR.
`configFetchTime` (seconds) is the time between each check of individual PRs. This is done to space out request to [the tracker](nixpk.gs).
`localNotify` (boolean) Enable local notifications.
`matrix.enable` (boolean) Enable matrix notifications.
`matrix.room` (string) Matrix room to send the notifications.
`matrix.ping` (boolean) Pings a user in the notification messages.
`matrix.userPing` and `matrix.userPingServer` (strings) are the required information for the ping.

### Usage

* Adding a PR : `nixpkgs-notifier add PR1 PR2 PR3 ...`
Example: `nixpkgs-notifier add 522460 522461`
* Removing a PR : `nixpkgs-notifier remove PR1 PR2 ...` or `nixpkgs-notifier rm`
Note : a PR will be automatically removed after the notification is sent.
* List tracked PR : `nixpkgs-notifier list`
* Launch listener : `nixpkgs-notifier listen`
(This is what periodically checks the PRs and handles the notifications) 
