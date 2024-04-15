# AbstractAI

Abstracts away various LLMs and provides a simple local Qt chat interface to interact with them, while focusing on the users ability to modify any part of a conversation with traceability.

Using ClassyFlaskDB, all interactions with LLMs and any modifications made to a conversation with them are logged with detailed source information to aid in filtering them for future training data.

This also implements speech to text as a type anywhere input method and several examples on text to speech using local models or a user deployed server.

## Installation

1. pip install ClassyFLaskDB from here: https://github.com/inventor2525/ClassyFlaskDB
1. pip install AbstractAI from this repo
3. Add model definitions to models.json (directions to come)
## Usage

### Linux
#### Chat Interface

```bash
cd <path to AbstractAI>
python AbstractAI/UI/main.py
```
Add models to models.json in ~/.config/AbstractAI/ to use them in the chat interface.
Config screen to come.

#### Speech to Text
Requires a server or modification to run locally.

Provides a simple interface to type anywhere using speech to text using a simple indicator in the top left of the screen.

Modify it to use a different key combo for transcribing using evtest to find the key codes, or simply left click the circle icon in the top left corner of the screen to toggle recording.

Common transcription APIs are not yet supported. This was built before they came out.

##### No-feedback mode
Transcribes all at once after user exits transcribe mode
```bash
cd <path to AbstractAI>
python AbstractAI/examples/record_keys.py
```

##### Talk typing feedback
Transcribes incrementally as the user speaks, using a small local model to provide feedback on what is being transcribed and a larger local or remote model to provide the final transcription.

```bash
cd <path to AbstractAI>
python AbstractAI/examples/record_keys2.py
```

# Why another chat app?
It will be more!

This was grown with the intent to do LLM control of a terminal, including the ability of an AI to code a whole project 'given a single prompt' like we now see projects springing up for seemingly every day (even if that is kinda a pipe dream at first).

I started working on this in early 2023 shortly after ChatGPT came out after experimenting with it's understanding of bash scripts, all other languages, and it's ability to write patch files. I wanted to provide an interface for it to do those things on it's own to avoid the back and forth copy paste that ChatGPT turned development into.

During that initial exploration I realized no such coding assistant or general personal assistant was going to work well unless task performing training data could be collected directly from the person interested in the task.

Current models are NOT trained to work through a development process, perform tasks, or add and remove code. They see diffs online, but they do not see the character stream that made those diffs.

This means that any such assistant program must first currently develop the mechanisms necessary to train future models. NOT waist time on current ones.

Anyone I figured who attempted to simply execute a task blind with such a model would fail to scale it to larger projects, simply because the model they are using is not trained to do what they want it to. To try and make that work is like trying to make a developer out of something that is trained from blogs, video transcripts, git commits, and reddit posts (sub par to a fiver bidder as George Hotz would say) because any current models are trained to predict next character in blogs and docs and COMPLETED code, not thought processes interspersed with character IO like we do in real development.

Unfortunately anyone to develop a tool first that lets the user correct the many mistakes of their virtual assistant dumber than a automated fiver autocomplete, is going to take too long for all the initial buzz, but it also means they're going to be gifted with so many models (each with so many different licenses or alignments) that you need to know where the data came from both to build something good in the future that isn't muddied with alignment and to obey any model's license who doesn't like you using their output to train another.

Given that no model is truly trained to do what we do as humans (lacking the data to do it), any system must first accept user corrections to it's responses before performing any tasks.

This is for the safety of your computer (who wants to give a random intern trained by Microsoft blind control of their computer for long), but it's also to re-train it with expert user examples, and git squash out the back and forth corrections we see in something like ChatGPT based development.

Thumbs up and thumbs down is not good enough here either. The already expert user needs to be able to correct it's mistakes before performing an action and those corrections need to be used for training, and where the user can not expertly correct it's mistakes, the back and forth conversation needs to be squashed into a corrected answer by the AI with human and TEST verification to ensure that that answer is good. For any code generation task, the code generated from the back and forth, IS your test. Traceability needs to be maintained however in that squash, not a simple delete of history, because if a jump in reasoning in the new answer is made, then it will not be trainable, so new 'step by step' thought processes will have to be generated and the easiest to train on one that gets the right answer, needs to be the one that is used for training data.

Filling the context window, no matter how large, with back and forth conversation and arguments with the ai, only degrades it's task performing capability. It is a fiver bidder! It needs it's jobs to be small, not looking at whole project source codes and months of email chains with you and it going back and forth. Thats not what you give a human, and it's a waist of money and energy to give to a bot. We break things down, why does it not get that benefit?

It needs USER controlled git squash. Not fiver AI git squash. NOTHING has been trained to do this, there is no "please summarize this" that works yet well enough to perform a useful task at scale without it massively degrading in performance and simply dropping requirements 1 after the other in quick succession during the development process, while adding others that it then gets confused about when you tell it not to use those.

Each thing in the conversation that contradicts or appends to another thing is a compute tick or layer to your NN that needs to be run in order to understand. That must be squashed out.

It also must remember where those edits came from because AI or other users could also be used to edit, and you need quality data which means you need to know where it came from. This also allows for any number of data augmentation techniques to be applied latter with traceability.

Additionally, large scale projects between multiple people, need issue and requirement tracking to scale. There has to be traceability between "Customer wants this thing" to "system shall be able to __" to "sub systems a, b and c must _" through all the code and to "developer write this function" to "tester write this test" and "docs write this doc".

You can't even give a person the task of 'summarize all of this' without breaking it down to a traceability of those different things and all that lie between them. So why in the heck would you give that blindly to an AI trained to write nice looking blog posts?

LLMs fundamentally as a matter of how they work do not even do well with counting their own words, this means they can not write a good diff because a diff includes line numbers at the top and any tokens you add to make it able to write better diffs is detracting from it's ability to write better code. They don't even repeat themselves well, they change their minds and add and remove comments or focus on white space. Telling them not to simply waists context space, and asking them to repeat themselves verbatim asks them to waist the customers money, they need to be trained in the usage of a CURSOR for task performing, not told to do a task they've never seen to produce some specific json format. You need data for that.

Given that they can generally do more than well enough to help a user somewhat however, the systems needed for task performing need to be there first because otherwise no one will use it given that they can ask a fiver ai with a nice custom parser, but initially.... it will suck at it. Working on those tools (custom diff formats, file readers, prompt generators & response parsers) though is a waist of time, they already exist.

It may be even that an instruction tuned model is not even what should be started with at all. Too much of it's responses are over fit to alignment type cookie cutter responses. If the context length is long enough, many expertly generated examples from the user themself, strung together 1 after another in random order actually provides a MUCH better response quality than trying to describe the task to an instruction tuned model, at least until fine tuning can occur. Instruction tuned models open up a door to faster development, but they are NOT designed for function calling, their training data is waisted on safety and warnings to the user and apologies to be of serious use, and while a larger model can have those things too, a larger model is more expensive and going to be eventually priced out.

The path to a cheap developer model is smallest, fastest, lowest energy required development model that performs task. That doesn't mean 7B param vs 70B or hundreds of billions or more, it means not waisted on other tasks and alignment.

Focusing on a function calling API of any specific model, or writing custom response parsing code is therefor a waist of time.... because you don't know if it's going to scale competitively in the future. And we, as people, do not use a custom parser. We use an IO stream with a fairly limited working memory that does not include an entire code base. This is the same logic tesla used with vision to dispel the need for lidar, they were right there, and it is right here.

Now... a Video audio IO stream would be great, but the first fully capable IO stream with the least latency and good enough throughput to work at scale, with the level of functionality that a complete 'developer' would need, is a shell. With a shell, you can do everything you need. You can run vim, you can install packages, you can setup a whole environment, you can even browse the web. You might not like 'more wget' as your web browser, but an LLM likes that just fine.

...But no one's trained an LLM to type in a terminal...

You see calls to commands using subprocess and the like, but not direct control of a terminal emulator through it's underlying IO stream. VT100 as a protocol offers all the functionality you need to give a model 'sight', and it already mostly understands it raw. Maybe all it needs is the screen buffer from a terminal emulator, maybe it would help to have the sequence of screen buffers over time, but VT100 gives it EVERYTHING. NO custom ide or parser of any form should EVER be needed on top of that. An AI could write a better OS and all software that you are using before it needs something between it and that.

Conversation data is multi model. If you talk to an AI about development, you paste in errors to the conversation, and you copy code docs user stories bug reports and references to and from. Terminal interaction IS part of the conversation, but no one tracks it or lets the user correct the models interactions with the terminal (however in-direct).

Typing in an IDE is how we interact as engineers, collecting that data is paramount to creating any sort of 'virtual developer', but the easiest way to do that with an LLM is to do it first with a terminal, not waisting time on VS code extensions or custom LLM response parsers or JSON formats.

Anyone who can make an LLM or agent (or even some multi agent pool with all the bells and whistles and even ability to question itself, simulate, or test before even responding to you), simply take instructions from a larger model that produces all the lazy "rest of code here" comments and forgets your 100s of requirements you spent all that time working on, and SIMPLY produces raw terminal interaction, is going to win this.

And it's a bit of a side note now, this is where much of my development time went, but... No pre prompt or model (speaking of data structures now) is good enough for everyone in tracking a projects life cycle. This is why there is SO MANY issue trackers and different development styles. NONE of them are one size fits all, so... any model that tracks all these interactions, conversations, source information, edits, etc... needs to be flexible. So, development time re-writing database boiler plate, needs to be removed (hens ClassyFlaskDB).

That being done now (if not a bit slow, but a good prototype), this is basically a local linux only (so far) 2023 ChatGPT clone that actually has search and the ability to edit responses. But thats just the beginning.

In order to train a good developer AI, you need interactions with it to be multi layered. There's the defining what the thing is you want, theres the thought process in your head as you develop something or as you're typing code, and there's actually interacting with the tools needed to make the thing. The first bit is the part everyone's so excited we now have and is trying to make something with, now that we do have it. The tools for the last bit is just a shell, it exists already and yet people keep waisting time re-making it to suite the use of the first bit... But no one is paying attention in any serious development that I've seen to the second bit. -- Thats the part we need to be recording, and we don't need neuralink here to start doing it.

People talk to themselves as they type. Listen to audio, provide a chat window to discuss development in general, and give the LLM a full terminal emulator that the user can take control of and correct when the AI goes wrong, and record the full IO of that emulator? THAT is the 'step by step' we need. Capture that, and the base models are already here to make a fairly good developer, fully open sourced. It doesn't need to write code good on it's own, it needs to be able to break down and remember tasks and requirements, write good questions for small tasks, and put code together. It can ask for help with the writing.

With custom parsers, you get a very incomplete re-development of nano and cat. With a shell? You get debuggers and linters and the web and performance monitoring tools and all of the logs and EVERYTHING.

But for that to work, we need to be able to collect data of actual developers doing actual development, tracking actual thought processes of why it is they just accessed one terminal application vs another in line with the actual shell IO stream of them writing code in vim.

From what I saw even all the way back in Feb 2023 though... it wouldn't take much data for that to work even just by consecutive example. You can coax a model through using PDB even just by repeated example and some format, but with a full shell... it doesn't need the format anymore, the base model already knows it, you just need to get it better at having some sort of objective.