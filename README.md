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

During that initial exploration I came to the conclusion that no such coding assistant or general personal assistant was going to work well unless task performing training data could be collected directly from the person interested in the task.

Current models are NOT trained to work through a development process, or add and remove code. They see diffs online, but they do not see the character stream that made those diffs.

In my view, this means that any such developer assistant program must first currently develop the mechanisms necessary to train future models capable of this. NOT waist time on current ones.

Anyone I figured who attempted to simply execute a task blind with such a model would fail to scale it to larger projects, simply because the model they are using is not trained to do what they want it to. To try and make that work is like trying to make a developer out of something that is trained from blogs, video transcripts, git commits, and reddit posts (sub par to a fiver bidder as George Hotz would say) because any current models are trained to predict next character in blogs and docs and COMPLETED code, not thought processes interspersed with character IO like we do in real development.

Unfortunately anyone to develop a tool first that lets the user correct the many mistakes of their virtual assistant dumber than a automated fiver trained autocomplete, was I figured going to take too long for all the initial buzz, but would also be gifted with so many models (each with so many different licenses or alignments) that you need to know where the data came from both to build something good in the future that isn't muddied (aka, over-fit!!) with 'alignment' and to obey any model's license who doesn't like you using their output to train another.

Given that no model is truly trained to do what we do as humans (lacking the data to do it), any system must first I figured accept user corrections to it's responses before performing any tasks.

This is for the safety of your computer (who wants to give a random intern, trained by Microsoft, blind control of their computer for long), but it's also to re-train it with expert user examples, and squash out the back and forth corrections we see in something like ChatGPT based development.

Thumbs up and thumbs down is not good enough here either. The already pre-assumed semi-expert user needs to be able to correct it's mistakes before performing an action and those corrections need to be usable for training and prompt engineering by example generation, and where the user can not expertly correct it's mistakes, the back and forth conversation needs to be squashed into a corrected answer by the AI with human and test verification to ensure that that answer is good. For any code generation task, the code generated from the back and forth is the start of your test.

Traceability needs to be maintained however in that conversation squash (similar to a git squash), not a simple delete of history, because if a jump in reasoning in the new answer is made, then it will not be trainable, so new 'step by step' thought processes will have to be generated and the easiest to train on one that gets the right answer, needs to be the one that is used for training data.

It's all well and good to assume general task following and a grounding on the entire internet worth of texts will be sufficient here along with a lengthy (inference expensive!) explanation by the prompter to execute your task(s) correctly and determine which one should be used, but while that now seems to be working fairly well... novel tasks can always benefit more I believe from user correction than prompt engineering.

Filling the context window, no matter how large, with back and forth conversation and arguments with the ai, only degrades it's task performing capability. It is a fiver bidder! It needs it's jobs to be small, not looking at whole project source codes and months of email chains with you and it going back and forth. Thats not what you give a human, and it's a waist of money and energy to give to a bot. We break things down, why does it not get that benefit?

On any novel task however (which is most of them since we're in un-charted territory): It needs USER controlled conversation squash as an option. It does not 'need' fiver AI conversation squash. NOTHING has been trained to do this, there is no "please summarize this" that works yet well enough to perform a useful task at scale without it massively degrading in performance and simply dropping requirements 1 after the other in quick succession during the development process, while adding others that it then gets confused about when you tell it not to use those.

Each thing in the conversation that contradicts or appends to another thing is a compute tick or layer to your NN that needs to be run in order to understand. That must be squashed out in order to scale.

You can add 1 million token context and 100s more layers even, but that is more expensive than squashing the conversation at each side bar. And the cheapest to perform the useful task, wins at that task.

Any assistant software with re-training and user edits in mind also must remember where those edits came from because AI or other users could also be used to edit, and you need quality data which means you need to know where it came from. This also allows for any number of data augmentation techniques to be applied latter with traceability.

Licenses could really add some roadblocks here for anyone to follow them too since the model used in the 'squash conversation' agent might not be the best one to use for coding or others. So for prototyping, you need to be able to use or try anything, but once you have a potentially commercially useful model or agent, you really need to know it's family tree and that of it's data. So, really, traceability is needed everywhere if you want to mix and match models from different companies, which given the un-knows here in what will be available tomorrow... you really need to be able to do, and you really need to be as confident as you can when doing it that your data isn't going to get you in legal trouble latter. Especially when this kind of software could open up a source for open or shared data that you don't want to just take from every model (legally).

I'm not a lawyer, but user correction I figured also could really add some portability to content licensing here, making it much more preferable to AI edits at first. Say I have a "great_company.AmazingGPT_vX". An edit or parade of that model (by a human, or by an AI) may still be usable in certain circumstance it wouldn't be otherwise. Chain of custody there could open up future training data as law makers decide things, and current copyright law is already fairly flushed out with human edits.

Additionally, large scale projects between multiple people, need issue and requirement tracking to scale. There has to be traceability between "Customer wants this thing" to "system shall be able to __" to "sub systems a, b and c must _" through all the code and to "developer write this function" to "tester write this test" and "docs write this doc".

You can't even give a person the task of 'summarize all of this project' without breaking it down to a traceability of those different things and all that lie between them. So why in the heck would you give the whole project and all email chains blindly to an AI trained to write nice looking blog posts when each time it's essentially going to have to redo that exploration and summarization?

Further, LLMs fundamentally as a matter of how they work do not even do well with counting their own words, this means they can not write a good diff because a diff includes line numbers at the top and any tokens you add to make it able to write better diffs is detracting from it's ability to write better code. They don't even repeat themselves well, they change their minds and add and remove comments or focus on white space. Telling them not to simply waists context space, and asking them to repeat themselves verbatim asks them to waist the customers money. They therefor need to be trained in the usage of a CURSOR for task performing, not told to do a task they've never seen to produce some specific json format. You need data for that.

Given that current LLMs and Agents built with them can generally do more than well enough to help a user somewhat, the systems needed for reduced task performing need to be there because otherwise no one will use it given that they can go ask a fiver ai with a nice custom parser that was easier to build than training a custom model, but those custom tools add a LOT of code debt and extra development that I don't believe is the way forward. Working on those tools (custom diff formats, file readers, prompt generators & response parsers) is in my opinion, a waist of time, because they already exist, directly usable through the terminal or a scripting language. There is no reason for a "tool" specific to AI use outside of the already existing functions methods and apps it can already directly call if guided or trained specifically to do so.

It may be even that an instruction tuned model is not even what should be started with at all. Too much of it's responses are over fit to alignment type cookie cutter responses. Some of the conversation style explanations to the user might be useful to help reasoning but frequently this is instructed out of instruction LLMs anyway, or the LLM is instructed to put its reasoning in a certain format block to not break the simple custom parser. But this adds a leap in reasoning that is separate from your task! If the context length is long enough, many expertly generated examples from the user themself, strung together 1 after another in random order actually provides a MUCH better response quality than trying to describe the task to an instruction tuned model, at least until fine tuning can occur, which once done, will ultimately lead to a MUCH cheeper inference. Instruction tuned models open up a door to faster development, but they are NOT designed for function calling, their training data is far too waisted on safety and warnings to the user and apologies to be of serious use, and while a larger model can have those things too, a larger model is more expensive and going to be eventually priced out.

The path to a cheap developer model is smallest, fastest, lowest energy required development model that performs task. That doesn't mean 7B param vs 70B or 100s of billions or more (like us, said loosely of course), it means not waisted on other tasks and alignment.

Focusing on a function calling API of any specific model, or writing custom response parsing code, or consuming whole code bases in ANY prompt is a waist of time because you don't know if it's going to scale competitively in the future. And we, as people, do not use a custom parser. We use an IO stream with a fairly limited working memory that does not include an entire code base. This is the same logic Tesla used with vision to dispel the need for lidar, they were right there, and it will I believe ultimately be right here.

It might be nice to imagine here a near infinite context as having the potential to do better than we can as humans one day soon even, but we started this AI journey with biological inspiration (perhaps with a poor lense and very over simplified, but it was inspired and re-inspired by biology repeatedly), and I think the fact that our working memory is actually quite small... Is pretty telling here what will happen. Large working memory is expensive, and it ALWAYS will be.

We are a stream processor! Not a db! -- And it is with these very good stream processors we are even talking about all this.

Now... a Video audio IO stream would be great, but the first fully capable IO stream with the least latency and good enough throughput to work at scale, with the level of functionality that a complete 'developer' would need, is a shell. With a shell, you can do everything you need. You can run vim, you can install packages, you can setup a whole environment, you can even browse the web. You might not like 'more wget' as your web browser, but an LLM likes that just fine.

...But no one's trained an LLM to type in a terminal...

You see calls to commands using subprocess and the like, but not direct control of a terminal emulator through it's underlying IO stream. VT100 as a protocol offers all the functionality you need to give a model 'sight', and it already mostly understands it raw. Maybe all it needs is the screen buffer from a terminal emulator, maybe it would help to have the sequence of screen buffers over time, but VT100 gives it EVERYTHING. NO custom ide or parser of any form should EVER be needed on top of that. An AI could write a better OS and all software that you are using before it needs something between it and that.

Conversation data is multi model. If you talk to an AI about development, you paste in errors to the conversation, and you copy code docs user stories bug reports and references to and from. Terminal interaction IS part of the conversation, but no one tracks it or lets the user correct the models interactions with the terminal (however in-direct).

Typing in an IDE is how we interact as engineers, collecting that data is paramount to creating any sort of 'virtual developer', but the easiest way to do that with an LLM is to do it first with a terminal, not waisting time on VS code extensions or custom LLM response parsers or JSON formats.

Anyone who can make an LLM or agent (or even some multi agent pool with all the bells and whistles and even ability to question itself, simulate, or test before even responding to you), simply take instructions from a larger model that produces all the lazy "rest of code here" comments and forgets your 100s of requirements you spent all that time working on, and SIMPLY produces raw terminal interaction, is going to win this.

And it's a bit of a side note now, this is where much of my development time went, but... No pre prompt or model (speaking of data structures now) is good enough for everyone in tracking a projects life cycle. This is why there is SO MANY issue trackers and different development styles. NONE of them are one size fits all, so... any model that tracks all these interactions, conversations, source information, edits, etc... needs to be flexible. So, development time re-writing database boiler plate, needs to be removed (hens ClassyFlaskDB).

That being done now (if not a bit slow, but a good prototype), this is basically a local linux only (so far) 2023 ChatGPT clone that actually has search, model switching during a conversation, local or remote storage and LLM execution, the ability to edit responses, and a entirely local python only interface I can run on a SBC or linux phone without needing to run a web host on it or deal with the extra layer of complexity added by web hosting and web development. But thats just the beginning.

In order to train a good developer AI, you need interactions with it to be multi layered. There's the defining what the thing is you want, theres the thought process in your head as you develop something or as you're typing code, and there's actually interacting with the tools needed to make the thing. The first bit is the part everyone's so excited we now have and is trying to make something with, now that we do have it. The tools for the last bit is just a shell, it exists already and yet people keep waisting time re-making it to suite the use of the first bit... But no one is paying attention in any serious development that I've seen to the second bit. -- Thats the part we need to be recording, and we don't need neuralink here to start doing it.

It's not just a terminal or a chat window you need. You need the chat window to be a AI training tool. And you need the terminal to be integrated with chat to have context. But you also need terminal replay to see what the model did or change it for re-training.

People talk to themselves as they type. Listen to audio for training data and faster typing, provide a chat window to discuss development in general, and give the LLM a full terminal emulator that the user can take control of and correct when the AI goes wrong, and record the full IO of that emulator? THAT is the 'step by step' we need. Capture that, and the base models are already here to make a fairly good developer, fully open sourced.

With custom parsers, you get a very incomplete re-development of nano and cat. With a shell? You get debuggers and linters and the web and performance monitoring tools and all of the logs and EVERYTHING.

But for that to work, we need to be able to collect data of actual developers doing actual development, tracking actual thought processes of why it is they just accessed one terminal application vs another in line with the actual shell IO stream of them writing code in vim, with the context of them explaining what they want.

From what I saw even all the way back in Feb 2023 though... it wouldn't take much data for that to work even just by consecutive example. You can coax a model through using PDB even just by repeated example and some format, but with a full shell... it doesn't need the format anymore, the base model already knows VT100, you just need to get it better at having some sort of objective.

During this development, we have been seeing ever more impressive base models, agent frameworks, and demos. I still believe a model trained in general terminal usage over specific custom tool use is the way to go for development agents however. Only with it do you get the level of tools needed to develop, essentially for free, and the ability with shell multiplexing to control and debug a larger multi app system (such as those in a typical robotic system - without having to write whole knew tools for that) or to use existing command line tools to copy paste to and from an expert (larger more expensive model) without having to waste tokens parakeeting it (badly!).

An automated developer could make anything else so in my mind, it really should come before anything else.

To make an "AI developer" however, you really need to augment the terminal <> user IO stream used in training, with a fuller layered conversation with the user, including their typical external facing conversation like what they would have with a product manager, as well as their more internal self murmur as they think through task execution. And creating such a dataset requires tools for voice and text interaction as well as conversation squashing, and terminal interaction in 1 package. Something you can use during real development.

It'd be nice to do that in a full featured IDE even like VS code, but while I prefer that even as my IDE for everyday use.... It requires not only more code to integrate with, but also more testing. A text only LLM like you can run on your own CPU even could potentially improve it's own code base even if it has a text based editor. If you rely on a GUI for primary development, then it has to test that as well. So... Some UI has to exist, I find a windowed GUI easier here for conversation editing and primary interaction, but ultimately... That should be fairly thin in order for the model to best be able to interact with it's own code base as soon as possible.

Looking back, I would have built the whole thing in a terminal app, but I figured OpenAI's models would get lazy at some point so I focused from the start on a ChatGPT like interface clone from the start so I could be sure I could access all future models in a common interface and be able to more easily search my conversations going forward... But ultimately, thats not likely the best interface for development, just the current primary access point.

Ultimately, I think at least 3 shells opened in a multiplexer would be better. One for chat with the LLM that it can see but not control so you can talk to the LLM switch conversations or edit but also show the model where in something you are talking about including problems with the app or any of your agents themselves. Then, another shell also showing the conversation window but that it can control so it can scan through instructions like a person would, and another for it to perform work in like apply edits or execute instructions. It could still add more terminals so it can interact with debuggers, profilers, other apps, servers, other systems, etc like a person would, but with those 3 I think you have about as rich of an interaction style you can possibly have with a text + optional audio only stream.

But... ChatGPT has long since caught the public eye, people are familiar, so we start there.