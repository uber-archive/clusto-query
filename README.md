`clusto-query` performs arbitrary boolean queries against clusto. It is available under the
ISC license, which you can find under `LICENSE.txt` and requires the python clusto libraries.

Infix expression operators are the following:

| Operator | Aliases | Meaning     |
|----------|---------| ------------|
| `=`      | `is` | equality    |
| `!=`     | `isnt`, `<>` | inequality  |
| `<=` | `le` | less than or equal to |
| `<` | `lt` | less than |
| `>=` | `ge` | greater than or equal to |
| `>` | `gt` | greater than |
| `^` | `startswith` | string starts with |
| `,` | `endswith` | string ends with |
| `contains` | | string contains |
| `in_cidr` | | IP address is in CIDR range |

Additionally, there are boolean operators and, or, and - (set subtraction)

some keywords (`pool`, `datacenter`, `clusto_type`, and `name`) can be directly queried
anything that's an "Attribute" must be prefixed with attr

Here's an example query:

    clusto_type = server and
    (attr system.cpucount >= 15 or attr system.memory >= 32760)
    and datacenter = peak-mpl1'

This query fetches all servers with more than 16 cores or 32768 MB of RAM
located in the "peak-mlp1" datacenter. Neato!

Note that I put in "15" instead of "16" intentionally; clusto's cpu counting
is off-by-one. That was fun. Let's go again:

    clusto_type contains "server" and
    (attr nagios.disabled = 1 - hostname endswith peak2)

This one finds all servers that are disabled in nagios and do not have a
hostname that ends in peak2.

Quoting and parens work the way you expect them to.

Run tests with `nosetests -w clusto_query --with-coverage`
